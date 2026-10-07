# RuiderCar v6.1.6
- Admin can configure homepage hero title and subtitle.
- Admin can configure hero width (%), height (px), title font size (px), and subtitle font size (px).
- Settings are stored in the existing system_settings table; no schema migration is required.
- Values are validated/clamped when rendered and text is HTML-escaped.
