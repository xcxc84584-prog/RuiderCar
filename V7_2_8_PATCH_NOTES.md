# RuiderCar v7.2.8
- 修正 IP 管理「全選目前搜尋結果」：改由 session-state selection set 作為唯一選取來源；搜尋、rerun 與批量操作後維持一致。
- 首頁公開商品改為 PostgreSQL LIMIT/OFFSET 真分頁，不再先載入全部商品後由 Python 切頁。
- 公開列表一次 JOIN 賣家資料，並只查目前頁面的封面 metadata；不在列表載入完整圖片 BLOB。
- 搜尋與價格條件使用 form，降低輸入過程的不必要 rerun。
- IP Identity 完整活動歷史改為明確 lazy load；未要求時不查 100 筆歷史。
- 遊客優先走公開商品輕量查詢；會員保留必要未讀狀態；管理員功能保持完整資料優先。
