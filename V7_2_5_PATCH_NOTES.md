# RuiderCar v7.2.5
- Administrator accounts are exempt from automatic request-rate Greylist enforcement and Active-IP Queue admission limits.
- Administrator request counts and IP activity logs continue to be recorded for observability.
- Existing manual IP blacklist behavior remains available after the one-time recovery.
- One-time safety recovery on deployment clears suspended/blacklisted/login-lock state for the configured ADMIN_EMAIL account and clears existing greylist/blacklist state on that administrator's account-scoped IP identity. A persistent system-setting marker prevents the recovery from repeating on later starts.
- Admin IP Management labels administrator identities as rate/queue exempt and hides irrelevant per-IP rate-limit editing controls for them.
