from agents.contact_memory_service import parse_contact_memory_request


def test_parse_contact_memory_request_stores_named_email() -> None:
    request = parse_contact_memory_request("store Evas email evabellova@gmail.com")

    assert request is not None
    assert request.display_name == "Evas"
    assert request.email_addresses == ["evabellova@gmail.com"]
    assert "evas" in request.aliases


def test_parse_contact_memory_request_stores_relationship_alias() -> None:
    request = parse_contact_memory_request("remember my brother James email james@example.com")

    assert request is not None
    assert request.display_name == "James"
    assert request.email_addresses == ["james@example.com"]
    assert "brother" in request.aliases
    assert "my brother" in request.aliases


def test_parse_contact_memory_request_ignores_non_contact_message() -> None:
    assert parse_contact_memory_request("find me best video on python") is None
