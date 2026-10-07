# RuiderCar v6.1
- Email verification uses pending_registrations. A users row is created only after successful verification.
- Admin member/blacklist management supports irreversible permanent account deletion with confirmation.
- General product selection is outside Streamlit forms so vehicle-only fields disappear immediately.
- Existing v6 functionality is retained.
- init_db/create_all creates pending_registrations automatically; migrations/v6_1.sql is included for manual PostgreSQL migration.
