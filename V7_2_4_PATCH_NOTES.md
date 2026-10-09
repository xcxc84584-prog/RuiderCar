# RuiderCar v7.2.4

- Streamlit Cloud localhost fallback now separates traffic identities by account: `127.0.0.1(account:<id>)`.
- Guests use a per-session fallback identity: `127.0.0.1(guest:<id>)`.
- Request-rate limits, grey/black/white state, queue state, custom request limits, and IP activity logs operate on the separated identity key.
- Login sessions store the same account-scoped identity so greylist/blacklist session revocation targets the matching account identity instead of every localhost user.
- Public/non-loopback addresses also retain account/guest suffixes at the application-management layer.
- IP identity columns are widened to 128 characters on PostgreSQL automatically.
- This is an application identity fallback, not proof of the user's true public IP.
