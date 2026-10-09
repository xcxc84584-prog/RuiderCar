# RuiderCar v7.2.6

- Default per-account storage quota: 100 MB.
- Administrator storage quota: Unlimited.
- Admin can configure a per-account storage quota from the IP + Account management view and restore the global default.
- Sidebar resource status shows current usage / limit for request rate and storage.
- Durable listing image bytes are counted toward the account storage quota.
- When a new image upload would exceed the quota, the upload is blocked and the user is asked whether to permanently remove the oldest deletable listing images to make room, or cancel.
- PostgreSQL/SQLite schema migration adds users.custom_storage_limit_mb.
