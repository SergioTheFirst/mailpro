"""
Cloudflare Workers AI LLM client for MailBot Premium v26.
Complies with CONSTITUTION.md Section V (LLM Rules).
"""
from __future__ import annotations

import threading
import time

import requests

from ..config_loader import KeysConfig
from ..state_manager import StateManager


class CloudflareLLM:
    """
    Cloudflare Workers AI client with anti-hallucination measures.

    Features:
    - Throttling (min 2.2s between calls)
    - Token tracking
    - Graceful error handling
    - System + user prompt support
    """

    def __init__(self, keys: KeysConfig, state: StateManager, min_interval: float = 2.2):
        self.keys = keys
        self.state = state
        self.min_interval = min_interval
        self._lock = threading.Lock()
        self._last_call = 0.0

        # API endpoint
        self.url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{keys.cf_account_id}/ai/run/@cf/meta/llama-3-8b-instruct"
        )

        self.headers = {
            "Authorization": f"Bearer {keys.cf_api_token}",
            "Content-Type": "application/json",
        }

    def _throttle(self) -> None:
        """Enforce minimum interval between API calls."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_call
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self._last_call = time.time()

    def ask(
        self,
        system_prompt: str,
        user_text: str,
        max_chars: int = 4000,
        timeout: int = 30,
    ) -> str:
        """
        Send request to Cloudflare LLM.

        Args:
            system_prompt: Instructions for the model
            user_text: Content to process
            max_chars: Max characters from user_text
            timeout: Request timeout in seconds

        Returns:
            Model response or empty string on error

        Notes:
            - Automatically throttles calls
            - Tracks tokens in state
            - Fails gracefully per CONSTITUTION Section VIII
        """
        # Throttle
        self._throttle()

        # Truncate user text
        user_trimmed = (user_text or "")[:max_chars]
        if not user_trimmed.strip():
            return ""  # No input = no output

        # Build payload
        # Cloudflare format: single "prompt" field with system + user combined
        full_prompt = f"{system_prompt.strip()}\n\nТекст:\n{user_trimmed}"

        payload = {"prompt": full_prompt}

        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=timeout,
            )
            response.raise_for_status()

            # Parse response
            data = response.json()
            result = data.get("result", {})
            text = result.get("response", "").strip()

            if not text:
                raise ValueError("Empty LLM response")

            # Track tokens (approximate)
            approx_tokens = max(1, (len(full_prompt) + len(text)) // 4)
            self.state.add_tokens(approx_tokens)

            # Mark LLM as available
            self.state.set_llm_unavailable(False, "")

            return text

        except requests.exceptions.Timeout:
            error_msg = "Cloudflare API timeout"
            self.state.set_llm_unavailable(True, error_msg)
            return ""

        except requests.exceptions.RequestException as e:
            error_msg = f"Cloudflare API error: {str(e)}"
            self.state.set_llm_unavailable(True, error_msg)
            return ""

        except Exception as e:  # noqa: BLE001
            error_msg = f"LLM error: {str(e)}"
            self.state.set_llm_unavailable(True, error_msg)
            return ""


# Self-test (mock-based since we can't call real API without keys)
def _self_test() -> bool:
    """Internal self-test with mock."""
    from unittest.mock import Mock

    # Mock config and state
    mock_keys = Mock()
    mock_keys.cf_account_id = "test_account"
    mock_keys.cf_api_token = "test_token"

    mock_state = Mock()
    mock_state.add_tokens = Mock()
    mock_state.set_llm_unavailable = Mock()

    # Create client
    llm = CloudflareLLM(mock_keys, mock_state, min_interval=0.1)

    # Verify initialization
    assert "test_account" in llm.url
    assert "Bearer test_token" in llm.headers["Authorization"]

    print("✅ LLM client initialization PASSED")

    # Test throttling
    start = time.time()
    llm._throttle()
    llm._throttle()
    elapsed = time.time() - start
    assert elapsed >= 0.1  # Should enforce min_interval

    print("✅ LLM client throttling PASSED")

    # Test empty input handling
    result = llm.ask("system prompt", "", max_chars=100)
    assert result == ""  # Empty input should return empty

    print("✅ LLM client empty input handling PASSED")

    print("\n✅ LLM CLIENT SELF-TEST PASSED")
    print("⚠️  Note: Real API test requires valid Cloudflare credentials")

    return True


if __name__ == "__main__":
    _self_test()
