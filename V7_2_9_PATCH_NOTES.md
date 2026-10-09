# RuiderCar v7.2.9

## Navigation
- IP 管理的「載入完整活動歷史」會保留 IP 管理分頁定位，不再回到 Dashboard。
- IP 管理相關 rerun 繼續使用 `admin_active_tab` 保存位置。

## Image optimization
- 新上傳 JPG/JPEG/PNG/WEBP 先由 Pillow 驗證與解碼。
- 最大像素數 24 MP，避免異常超大圖片。
- 修正 EXIF orientation，最大長邊縮至 1600 px。
- 持久化前統一壓縮為 WEBP quality 82。
- 商品卡封面另外生成 640 px / WEBP quality 72 的記憶體快取版本，避免列表傳輸完整 detail image。
- Storage quota 依壓縮後實際 bytes 計算。

## Progressive loading / prefetch
- 當前頁 P0 資料先渲染。
- 首頁目前商品 detail metadata 在畫面輸出後預取。
- 前一頁、下一頁 catalog 資料在 P2 階段預取，TTL 20 秒。
- Detail 查詢會優先命中預取 detail cache。
- 返回首頁時原頁面通常已存在短期 cache，並保留原商品定位。
- 安全狀態（session/blacklist/greylist/authorization）不納入此公開商品 cache。
