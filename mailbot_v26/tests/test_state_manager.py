from datetime import datetime
from datetime import datetime
from pathlib import Path

from mailbot_v26.state_manager import StateManager


def test_state_persistence(tmp_path: Path) -> None:
    state_path = tmp_path / "state.json"
    manager = StateManager(state_path)
    manager.update_last_uid("user@example.com", 10)
    manager.update_check_time("user@example.com", datetime(2024, 1, 1))
    manager.add_tokens(50)
    manager.save(force=True)

    manager2 = StateManager(state_path)
    assert manager2.get_last_uid("user@example.com") == 10
    ts = manager2.get_last_check_time("user@example.com")
    assert ts is not None and ts.year == 2024
    assert manager2._state.llm.tokens_used_today >= 50


def test_llm_unavailable_flag(tmp_path: Path) -> None:
    manager = StateManager(tmp_path / "state.json")
    manager.set_llm_unavailable(True, "maintenance")
    manager.save(force=True)
    reloaded = StateManager(tmp_path / "state.json")
    assert reloaded._state.llm.unavailable is True
    assert reloaded._state.llm.last_error == "maintenance"
