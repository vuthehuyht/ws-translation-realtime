"""Unit tests for User Request Schemas (app.schemas.requests.user)."""

import pytest
from pydantic import ValidationError

from app.schemas.requests.user import DeleteAccountRequest


def test_delete_account_request_requires_exact_delete_confirmation() -> None:
    valid = DeleteAccountRequest(confirmation="DELETE")
    assert valid.confirmation == "DELETE"

    for invalid_value in ("delete", "Delete", "YES", "", "DELETE "):
        with pytest.raises(ValidationError):
            DeleteAccountRequest.model_validate({"confirmation": invalid_value})
