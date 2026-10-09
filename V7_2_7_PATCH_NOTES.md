# RuiderCar v7.2.7

- IP 管理新增搜尋結果全選與批量刪除 IP Identity；一般 LOG 一併刪除，GREYLIST 歷史依既有永久保留規則保留。
- IP request limit 與 Account storage limit 改為全站統一政策。一般帳號不再套用個別 override；Administrator 與 Whitelist 為 Unlimited exemption。
- 管理員儲存系統設定後清除舊的 custom_request_limit / custom_storage_limit_mb，統一發佈最新全站限制。
- IP 管理操作後保留 IP管理 tab，並保留既有搜尋/狀態元件 session state。
- IP 狀態更新與批量刪除加入操作進度條。
- Sidebar 資源狀態維持 current usage / effective limit 顯示；Administrator / Whitelist 顯示 current usage / Unlimited。
