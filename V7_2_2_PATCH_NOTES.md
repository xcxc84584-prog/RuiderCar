# RuiderCar v7.2.2
- Streamlit Cloud localhost/unknown IP safe-mode: diagnostic logging remains, IP blocking/greylisting/queue is not enforced when the app cannot distinguish a real client IP.
- IP diagnostics shown in Admin > IP Management.
- General IP activity logs can be deleted individually, per IP, or cleared in bulk.
- GREYLIST events are excluded from retention cleanup and kept until an administrator explicitly deletes them.
- Greylist History is a separate Admin section; collapsed view shows the latest record only, expanded view loads all retained history.
- Greylist history deletion does not change current IP status.
- Asia/Taipei remains the display/export timezone.
