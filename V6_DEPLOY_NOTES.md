# RuiderCar v6 deployment notes

## Database migration
`backend.database.init_db()` performs idempotent PostgreSQL/SQLite migration before ORM queries.
Manual SQL is also available at `migrations/v6.sql`.

## Streamlit Secrets required for Email verification
- `RESEND_API_KEY`
- `EMAIL_FROM`

`EMAIL_FROM` must be a sender/domain accepted by your email provider.

## v6 changes
- Email verification with 6-digit code, 10-minute expiry, 60-second resend cooldown.
- Vehicle/general product types.
- Browse filters: vehicle-only and image/table mode.
- Admin forced removal requires a reason, sends an internal notification, then permanently removes the listing and images.
- User traffic state is refreshed from DB on each Streamlit rerun.
- Mail/traffic pages include explicit refresh controls.
- Vehicle mileage is rendered with full thousands-separated value.
