from datetime import date, timedelta

from api.leave_reset_api import cancel_leave_for_date_if_exists
from pages.leave_request_page import LeaveRequestPage
from pages.login_page import LoginPage
from utils.data_reader import load_leave_request_data


def test_create_leave_request(page):
    """Employee applies leave: tomorrow, first half → second half, then submits."""
    data = load_leave_request_data()
    leave_date = date.today() + timedelta(days=1)

    # Same-day guard: cancel existing leave via API, or no-op and create fresh.
    cancel_leave_for_date_if_exists(
        leave_date,
        email=data["email"],
        password=data["password"],
    )

    login_page = LoginPage(page)
    leave_page = LeaveRequestPage(page)

    login_page.login(data["email"], data["password"])
    leave_page.create_leave_request(
        leave_type_name=data["leave_type_name"],
        leave_type_code=data["leave_type_code"],
        reason=data["reason"],
        leave_date=leave_date,
        start_session=data["start_session"],
        end_session=data["end_session"],
    )
