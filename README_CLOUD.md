# RuiderCar Cloud 部署版

此壓縮檔已清除測試 DB、測試會員、示範商品、測試圖片與備份資料。

## Streamlit Community Cloud
1. 將 `RuiderCar/` 內容推送到 GitHub repository。
2. Streamlit Community Cloud 建立 App，Main file path 選 `app.py`。
3. 在 App settings → Secrets 貼入 `.streamlit/secrets.toml.example` 的欄位並換成真實值。
4. `DATABASE_URL` 必須指向外部 PostgreSQL，否則未設定時會回退到本機 SQLite；Cloud 重新部署時本機 SQLite 不保證持久。
5. 首次啟動會建立資料表與唯一管理員帳號；不會建立 Demo User 或示範商品。
6. 管理員登入後先到「系統設定」填入收款銀行、戶名、銀行帳號與轉帳說明。

## 本版修正
- 一般信件區：寄件者帳號名、Email、電話；未讀/已讀切換；快速回信。
- 管理員信箱：寄件者帳號名、Email、電話；未讀/已讀/處理中/已回覆/已關閉；快速回信。
- 流量中心：直接展示管理員於系統設定維護的收款銀行、戶名、帳號與轉帳說明。
- 清除全部測試資料。

## 注意
商品圖片目前仍使用 `storage/uploads` 本機檔案。Streamlit Community Cloud 的本機檔案系統不是可靠的永久物件儲存；正式公開營運前應再接 S3/R2/Supabase Storage 等持久化物件儲存。
