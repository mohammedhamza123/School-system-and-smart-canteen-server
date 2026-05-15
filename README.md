# School-system-and-smart-canteen-server

Smart School Canteen Backend (FastAPI)

## Run

1. Create virtual env and activate.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Start API:
   - `uvicorn app.main:app --reload`

The API starts with:
- base path: `/api/v1`
- health check: `/health`
- default admin login:
  - username: `admin`
  - password: `Admin@123`

## Admin Account Settings

- `GET /api/v1/users/admin/settings`: get system admin settings.
- `PUT /api/v1/users/admin/settings`: update system admin settings.
- Both endpoints require an admin bearer token.

## Feature Modules

Each feature follows:

```
feature_name/
├── router.py
├── service.py
├── model.py
├── schema.py
├── repository.py
└── utils.py
```

Detailed module documentation exists in `MODULES.md`.
