import pytest
from fastapi import HTTPException

from backend.core.safety import normalize_session_id, sanitize_upload_filename


def test_normalize_session_id_accepts_safe_ids():
    assert normalize_session_id("session-123_ok.1") == "session-123_ok.1"


@pytest.mark.parametrize(
    "session_id",
    ["../escape", "bad/path", "", "a" * 65, "space value", "$invalid"],
)
def test_normalize_session_id_rejects_unsafe_ids(session_id):
    with pytest.raises(HTTPException):
        normalize_session_id(session_id)


def test_sanitize_upload_filename_removes_path_segments_and_symbols():
    assert sanitize_upload_filename("../../Market Report Q1!!.PDF") == "Market_Report_Q1.pdf"


def test_sanitize_upload_filename_handles_windows_path_segments():
    assert sanitize_upload_filename(r"..\..\secret report.md") == "secret_report.md"


def test_sanitize_upload_filename_keeps_safe_default_for_empty_name():
    assert sanitize_upload_filename("") == "upload"
