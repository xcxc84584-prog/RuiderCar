# RuiderCar v7.1.2

## Registration
- Added Normal Registration and Authorized Registration.
- Normal Registration is limited by the configured normal-account limit.
- Authorized Registration bypasses the normal-account limit but starts in `pending_approval` and cannot log in until an administrator approves it.
- Added administrator approval/rejection UI and account status fields.

## Guest Favorites
- Guests can favorite/unfavorite active listings without an account.
- Guest favorite IDs are stored in the current browser cookie for up to 365 days.
- Guest favorites automatically merge into the member Favorites table after login and are deduplicated.
- Guest favorites are browser/device-local and are not cross-device synchronized.

## Security Hardening
- Added service-layer administrator checks to administrator mailbox, traffic review, settings, blacklist/member listing, registration approval, and backup operations.
- Message sender identity is bound to the authenticated user ID at the service boundary.
- Added five-failure login lockout for 15 minutes for existing accounts.
- Pending/rejected authorized accounts cannot create or restore login sessions.
- Administrator impersonation now blocks inactive/suspended/blacklisted targets.
- Added administrator audit log table and logging for impersonation start/end and authorized-registration decisions.
- Password hashing remains PBKDF2-HMAC-SHA256 with 600,000 iterations and per-password random salt.

## Still pending
- Email ownership verification.
- Phone OTP ownership verification.
- True HttpOnly remember-session cookie (limited by the current Streamlit cookie integration).
- Full Git-history secret scan and production log secret scan should be performed against the deployed repository/environment.
