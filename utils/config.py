# HRMS URLs and API endpoints (single source for tests + api helpers).
# API host must match the live web app (`NEXT_PUBLIC_API_URL` → hrms-api.encoresky.tech).
BASE_URL = "https://hrms.eznity.ai"
API_BASE = "https://hrms-api.encoresky.tech"
API_URL = f"{API_BASE}/api/v1"
EMPLOYEE_DELETE_URL = f"{API_BASE}/company/api/v1/employees/delete"
LEAVE_MY_REQUESTS_URL = f"{API_BASE}/leave/api/v1/leave-requests/my-requests"
LEAVE_REQUESTS_URL = f"{API_BASE}/leave/api/v1/leave-requests"

VALID_USER = {
    "email": "deepti.chouhan@encoresky.com",
    "password": "Test@123",
}
