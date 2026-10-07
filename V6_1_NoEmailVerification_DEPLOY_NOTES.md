# RuiderCar v6.1 No Email Verification
- Registration creates the user immediately after normal field validation.
- No verification code, Resend API, pending registration, or Email verification UI.
- New users are created with verified=True for compatibility with the existing schema.
- Admin permanent account deletion remains.
- General-product dynamic form remains: vehicle fields disappear immediately when 常規商品 is selected.
- Existing product/traffic/blacklist functionality is retained.
- Existing pending_registrations table in PostgreSQL may remain unused; it does not affect operation.
