from app.security.rbac import can_access, filter_authorized_sources


def test_admin_has_all_access():
    assert can_access("Admin", "finance_db")
    assert can_access("Admin", "employee_records")


def test_engineer_cannot_access_hr_records():
    assert can_access("Engineer", "logs")
    assert not can_access("Engineer", "employee_records")


def test_filter_authorized_sources():
    authorized, denied = filter_authorized_sources("Finance", ["finance_db", "employee_records"])
    assert authorized == ["finance_db"]
    assert denied == ["employee_records"]
