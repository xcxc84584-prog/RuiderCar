# RuiderCar v6.2.2
- Product images are now stored persistently in PostgreSQL/Supabase (`listing_images.image_data`) instead of relying on Streamlit Cloud local disk.
- Legacy local images are migrated into the database when the old file is still available. Images already lost in a prior redeploy cannot be reconstructed and must be uploaded once again.
- New images: max 10 per listing, max 5 MB each.
- Added Favorites (`favorites` table), detail-page favorite toggle, and a new `我的收藏` browsing page.
- Administrator sessions are not subject to the normal device-registration marker restriction.
- Admin member/blacklist UI now includes `強制登入／切換成此帳號`.
- Admin impersonation does not replace the administrator's persistent login cookie; a `返回管理員帳號` control restores the admin session.
- Deleted/anonymized accounts cannot be impersonated.
- Automatic database migration is included; no manual SQL is required.
