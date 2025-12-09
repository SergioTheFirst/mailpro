"""Cloudflare AI client wrapper.

The client is deliberately lightweight and defensive. If credentials are
missing or a request fails, the caller receives an empty string to keep
pipeline stability, satisfying Constitution Section VI.1.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CloudflareConfig:
    account_id: str
    api_token: str
    model: str = "@cf/meta/llama-3-8b-instruct"


class CloudflareLLMClient:
    """Minimal Cloudflare AI REST client."""

    def __init__(self, config: CloudflareConfig) -> None:
        self.config = config

    def _build_request(self, prompt: str, data: str) -> urllib.request.Request:
        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self.config.account_id}/ai/run/{self.config.model}"
        )
        payload = json.dumps(
            {
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": data},
                ]
            }
        ).encode("utf-8")

        request = urllib.request.Request(url, data=payload, method="POST")
        request.add_header("Authorization", f"Bearer {self.config.api_token}")
        request.add_header("Content-Type", "application/json")
        return request

    def generate(self, prompt: str, data: str) -> str:
        """Return model output or empty string on failure."""
        if not self.config.account_id or not self.config.api_token:
            return ""

        try:
            request = self._build_request(prompt, data)
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read().decode("utf-8")
            parsed = json.loads(body)
            choices = parsed.get("result", {}).get("response", {})
            if isinstance(choices, dict) and "message" in choices:
                content = choices["message"].get("content", "")
            else:
                content = parsed.get("result", {}).get("output", "")
            if isinstance(content, list):
                content = "".join(str(part) for part in content)
            return str(content).strip()
        except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError, ValueError):
            return ""


def load_prompt(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()
