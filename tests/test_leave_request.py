from datetime import date, timedelta

from api.leave_reset_api import (
    cancel_leave_for_date_if_exists,
    cancel_leaves_overlapping_range_if_exist,
)
from pages.leave_request_page import LeaveRequestPage
from pages.login_page import LoginPage
from utils.data_reader import load_leave_request_data, load_sandwich_leave_request_data
from utils.leave_dates import next_weekend_sandwich_pair


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


def test_create_weekend_sandwich_leave(page):
    """
    Friday leave + Monday leave with weekend between → sandwich days on Monday request.

    Requires leave policy with sandwich-on-weekends enabled (e.g. leave_type_Automation).
    """
    data = load_sandwich_leave_request_data()
    friday, monday = next_weekend_sandwich_pair()

    cancel_leaves_overlapping_range_if_exist(
        friday,
        monday,
        email=data["email"],
        password=data["password"],
    )

    login_page = LoginPage(page)
    leave_page = LeaveRequestPage(page)

    login_page.login(data["email"], data["password"])
    leave_page.create_weekend_sandwich_leaves(
        friday=friday,
        monday=monday,
        leave_type_name=data["leave_type_name"],
        leave_type_code=data["leave_type_code"],
        reason_before_weekend=data["reason_before_weekend"],
        reason_after_weekend=data["reason_after_weekend"],
        start_session=data["start_session"],
        end_session=data["end_session"],
    )
