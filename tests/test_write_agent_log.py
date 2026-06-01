import pytest

from agents.write_agent_log import build_log_payload


def test_build_log_payload_strips_message() -> None:
    assert build_log_payload("  first log entry  ") == {"message": "first log entry"}


def test_build_log_payload_rejects_empty_message() -> None:
    with pytest.raises(ValueError, match="Message cannot be empty"):
        build_log_payload("   ")
