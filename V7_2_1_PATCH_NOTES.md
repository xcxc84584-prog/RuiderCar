# RuiderCar v7.2.1
- IPv4-mapped IPv6 addresses such as `::ffff:127.0.0.1` are normalized to IPv4.
- Migrated Streamlit `use_container_width` calls to the current `width` API.
- IP request-rate accounting is separated from persistent VISIT logs; VISIT history is throttled to at most one record per IP every 30 seconds while every app request is still counted.
- User-facing IP timestamps and exported IP CSV timestamps use Asia/Taipei (UTC+8). Database timestamps remain UTC internally for safe comparisons.
- Appointment date/time defaults use Taiwan local time.
- Added automatic migration fields for the per-IP one-minute request counter.
