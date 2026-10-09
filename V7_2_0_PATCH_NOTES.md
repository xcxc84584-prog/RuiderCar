# RuiderCar v7.2.0

## 本版重點

1. 頁面切換加入載入進度提示。
2. 首頁無圖片商品卡將標題與價格分行顯示。
3. 管理員新增「IP管理」。
4. 記錄 IP 首次訪問、最後活動、應用層 requests/min、最高速率、狀態與活動紀錄。
5. IP 可由管理員設為一般、白名單、黑名單；灰名單由速率規則自動建立。
6. IP LOG 可下載 CSV。
7. 系統設定新增：每 IP 最大請求數/分鐘（預設 180）、Active IP 上限（預設 50）、IP LOG 保存天數（預設 7）。
8. Active IP 定義為最近 5 分鐘有活動；超過上限的新 IP 進入 Queue，白名單不受 Queue 限制。
9. 超過 request rate 門檻，自動 Greylist 30 分鐘並撤銷該 IP 綁定的登入 Session。
10. IPv4/IPv6 正規化。

## 技術說明

- requests/min 為 RuiderCar 應用層活動速率，不宣稱是真實網路 Mbps。
- Client IP 優先使用 Streamlit context 提供的 IP；Proxy Header 僅作平台環境下的 best-effort fallback，IP 不作為帳號認證身分。
- PostgreSQL admission 判斷使用 advisory transaction lock 降低同時入站造成的競爭條件。
- 新增資料表 `ip_address_records`、`ip_activity_logs`，並為 `login_sessions` 新增 `ip_address` 欄位；由啟動流程自動建立/遷移。
