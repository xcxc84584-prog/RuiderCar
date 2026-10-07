# RuiderCar Vehicle Marketplace - FIXED

完整 Streamlit 分層專案，已修正：
- SQLite `unable to open database file`
- Portable Python 缺少 `venv`
- `passlib` / `bcrypt` 相容性與 72-byte 錯誤
- 備份服務相對路徑問題

## 專案結構
- `frontend/`：Streamlit UI、頁面、藍色商品卡、深色主題
- `backend/`：資料庫、認證、商品、預約、信件、流量、管理員、備份
- `data/`：本機 SQLite
- `storage/`：上傳檔與備份
- `app.py`：Streamlit Cloud 入口

## Portable Python 本機執行
不需要建立 `.venv`。

```powershell
cd "你的 VehicleMarketStreamlitFull_FIXED 路徑"
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

若 `python` 不是 Portable Python：
```powershell
& "E:\PortableEnvironment v1\WebDev\Python\python.exe" -m pip install -r requirements.txt
& "E:\PortableEnvironment v1\WebDev\Python\python.exe" -m streamlit run app.py
```

## 測試帳號
管理員：
- Email: `admin@example.com`
- Password: `ChangeMe123!`

一般會員：
- Email: `demo@example.com`
- Password: `Demo123!`

公開部署前請更換測試管理員帳號與密碼。

## 密碼
本版不使用 `passlib` / `bcrypt`。
改用 Python 標準函式庫 `hashlib.pbkdf2_hmac("sha256")` + 隨機 salt + `hmac.compare_digest()`。

## SQLite
本機資料庫會固定建立在：
`<PROJECT_ROOT>/data/vehicle_market.db`

因此不依賴 PowerShell 的 current working directory。

## Streamlit Community Cloud
SQLite 只適合本機與 Demo。正式營運請使用外部 PostgreSQL，並透過 `DATABASE_URL` 設定連線；照片與附件應使用持久化物件儲存。
網站程式更新不得以刪除資料庫重新建立的方式進行。

## 目前功能
- 深色 UI + 藍色商品卡
- 訪客瀏覽
- 註冊 / 登入
- Email / 手機唯一性
- 商品草稿 / 上架
- 預約：買家提出 → 賣家確認
- 站內信
- 送信給管理員
- 管理員信箱
- TrafficTransaction
- 流量購買與管理員審核
- 初始流量設定
- 管理員系統設定
- 管理員備份下載


## RuiderCar build fixes
- Seller drafts can be reopened and edited.
- Publish action now keeps insufficient-traffic errors visible instead of immediately rerunning.
- Successful publish deducts traffic once and updates the session balance.
- Persistent refresh-login patch is included.

## 商品照片
- 每個商品最多 10 張照片。
- 支援 JPG/JPEG/PNG/WEBP。
- 第 1 張照片自動作為首頁商品卡封面。
- 賣家可在「我的商品」新增、刪除及左右調整照片順序。
- 商品詳細頁展示所有照片。
- 圖片存放於 storage/uploads/listings/<listing_id>/，資料庫 listing_images 保存路徑與排序。

## 草稿永久刪除
- 草稿商品提供「刪除草稿」。
- 必須經過二次確認。
- 只有商品擁有者可刪除，且僅限 draft 狀態。
- 同步刪除 listing_images 資料及 storage/uploads/listings/<listing_id>/ 圖片目錄。
- 草稿刪除不新增 TrafficTransaction，也不影響流量餘額。

## 商品下架與退款
- active 商品提供「下架商品」，必須二次確認。
- 下架後商品回到 draft，首頁立即不再公開，但商品資料與照片保留。
- 僅按實際剩餘刊登時間比例退還刊登時間費（200 × 月數）；價格係數費與類別低消不退。
- 每次上架記錄 published_at / expires_at / listing_time_fee；下架退款寫入 TrafficTransaction。
- 下架後重新上架會建立新的上架週期並重新計算上架費，避免同一週期重複退款。
- SQLite 啟動時採 additive schema migration，不需要刪除既有 DB。
