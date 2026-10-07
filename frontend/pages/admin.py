import streamlit as st
from backend.services.admin_service import settings,save_setting,users_for_admin,blacklist_user,unblacklist_user,permanently_delete_user
from backend.services.message_service import admin_messages,reply_admin,set_admin_message_status
from backend.services.traffic_service import pending,approve,reject
from backend.services.backup_service import make_backup

def render():
    if st.session_state.user.get("role")!="admin":st.error("沒有管理員權限");return
    st.title("管理員後台")
    tabs=st.tabs(["Dashboard","會員／黑名單","管理員信箱","流量審核","系統設定","資料備份"])
    with tabs[0]:
        st.info("管理員後台。")
    with tabs[1]:
        users=users_for_admin()
        c1,c2=st.columns([3,1])
        keyword=c1.text_input("搜尋會員",placeholder="輸入會員 ID、姓名、Email 或手機",key="admin_user_search").strip().lower()
        show_deleted=c2.checkbox("顯示已註銷帳戶",value=False,key="admin_show_deleted")
        if not show_deleted:
            users=[u for u in users if not u["deleted"]]
        if keyword:
            users=[u for u in users if keyword in str(u["id"]).lower() or keyword in u["name"].lower() or keyword in u["email"].lower() or keyword in u["phone"].lower()]
        st.caption(f"搜尋結果：{len(users)} 位")
        if not users:st.info("沒有符合條件的會員。")
        for u in users:
            status="已註銷" if u["deleted"] else ("黑名單" if u["blacklisted"] else "正常")
            with st.expander(f'#{u["id"]} [{status}] {u["name"]}｜{u["email"]}'):
                st.caption(f'電話：{u["phone"]}｜角色：{u["role"]}｜流量：{u["traffic_balance"]}｜註冊：{u["created_at"]}')
                if u["deleted"]:
                    st.info("此帳戶已註銷，僅保留歷史資料，不提供黑名單操作。")
                elif u["blacklisted"]:
                    st.error(f'黑名單原因：{u["blacklist_reason"]}')
                    st.caption(f'加入時間：{u["blacklisted_at"]}')
                    if st.button("解除黑名單",key=f'unblack_{u["id"]}',use_container_width=True):
                        ok,msg=unblacklist_user(u["id"])
                        (st.success if ok else st.error)(msg)
                        if ok:st.rerun()
                elif u["role"]!="admin":
                    reason=st.text_input("加入黑名單原因",key=f'black_reason_{u["id"]}',placeholder="例如：詐騙疑慮、違反平台規則")
                    if st.button("加入黑名單",key=f'black_{u["id"]}',type="primary",use_container_width=True):
                        ok,msg=blacklist_user(u["id"],reason)
                        (st.success if ok else st.error)(msg)
                        if ok:st.rerun()
                else:
                    st.info("管理員帳號不可加入黑名單。")
                if u["role"]!="admin":
                    st.divider()
                    st.error("危險操作：徹底刪除會移除此帳號及其平台關聯資料，無法復原。")
                    confirm=st.checkbox("我確認要永久刪除此帳號及相關資料",key=f'permadelete_confirm_{u["id"]}')
                    if st.button("徹底刪除帳號",key=f'permadelete_{u["id"]}',type="primary",use_container_width=True,disabled=not confirm):
                        ok,msg=permanently_delete_user(st.session_state.user["id"],u["id"])
                        (st.success if ok else st.error)(msg)
                        if ok:st.rerun()
    with tabs[2]:
        rows=admin_messages()
        if not rows:st.info("目前沒有管理員信件。")
        for m in rows:
            with st.expander(f'#{m["id"]} [{m["status"]}] {m["subject"]}｜{m["user_name"]}'):
                st.caption(f'帳號名：{m["user_name"]}｜信箱：{m["user_email"]}｜電話：{m["user_phone"]}')
                st.caption(f'類型：{m["category"]}｜送出時間：{m["created_at"]}')
                st.write(m["body"])
                statuses=["未讀","已讀","處理中","已回覆","已關閉"]
                idx=statuses.index(m["status"]) if m["status"] in statuses else 0
                c1,c2=st.columns(2)
                ns=c1.selectbox("狀態",statuses,index=idx,key=f'ams_{m["id"]}')
                if c2.button("更新狀態",key=f'amsb_{m["id"]}',use_container_width=True):
                    set_admin_message_status(m["id"],ns);st.rerun()
                r=st.text_area("快速回信",value=m["reply"],key=f'r{m["id"]}')
                if st.button("回覆並標記已回覆",key=f'rr{m["id"]}',type="primary",use_container_width=True):
                    if reply_admin(m["id"],r):st.rerun()
                    else:st.error("回覆內容不可為空")
    with tabs[3]:
        rows=pending()
        if not rows:st.info("目前沒有等待審核的流量購買申請。")
        for r in rows:
            with st.container(border=True):
                st.write(f'申請 #{r["id"]}｜會員 {r["user_id"]}｜NT$ {r["amount"]}｜末五碼 {r["last5"]}')
                st.caption(f'申請時間：{r["created_at"]}')
                if r.get("note"):st.write(f'備註：{r["note"]}')
                c1,c2=st.columns(2)
                if c1.button("批准",key=f'ap{r["id"]}',type="primary",use_container_width=True):
                    ok,msg=approve(r["id"])
                    (st.success if ok else st.error)(msg)
                    if ok:st.rerun()
                if c2.button("拒絕",key=f'rj{r["id"]}',use_container_width=True):
                    ok,msg=reject(r["id"])
                    (st.success if ok else st.error)(msg)
                    if ok:st.rerun()
    with tabs[4]:
        s=settings()
        initial=st.number_input("新會員初始流量",min_value=0,value=int(s.get("initial_traffic","1000")))
        traffic_max=st.number_input("單商品每年流量上限",min_value=1,value=int(s.get("traffic_max","100")))
        traffic_min=st.number_input("單商品最低流量",min_value=1,value=int(s.get("traffic_min","20")))
        traffic_per=st.number_input("每 10 萬元／每月流量",min_value=1,value=int(s.get("traffic_per_100k_month","5")))
        st.caption("計算：ceil(商品價格 ÷ 100,000) × 上架月數 × 每10萬元每月流量，再套用最低與最高限制。1 流量 = NT$1。")
        email=st.text_input("管理員信箱",value=s.get("admin_email",""))
        bank=st.text_input("收款銀行",value=s.get("bank_name",""))
        holder=st.text_input("收款戶名",value=s.get("bank_holder",""))
        account=st.text_input("收款銀行帳號",value=s.get("transfer_account",""))
        transfer_note=st.text_area("流量購買/轉帳說明",value=s.get("transfer_note",""))
        st.divider()
        st.subheader("首頁標頭設定")
        hero_title=st.text_input("標題內容",value=s.get("home_hero_title","RuiderCar 商品交易平台"))
        hero_subtitle=st.text_area("副標題內容",value=s.get("home_hero_subtitle",""))
        hc1,hc2=st.columns(2)
        hero_width=hc1.number_input("標頭寬度（%）",min_value=40,max_value=100,value=int(s.get("home_hero_width","100")),step=1)
        hero_height=hc2.number_input("標頭高度（px）",min_value=80,max_value=400,value=int(s.get("home_hero_height","140")),step=10)
        hc3,hc4=st.columns(2)
        hero_title_size=hc3.number_input("標題字號（px）",min_value=16,max_value=64,value=int(s.get("home_hero_title_size","26")),step=1)
        hero_subtitle_size=hc4.number_input("副標題字號（px）",min_value=10,max_value=32,value=int(s.get("home_hero_subtitle_size","16")),step=1)
        st.caption("寬度以首頁內容區百分比設定；高度與字號使用 px。")
        if st.button("儲存系統設定",use_container_width=True):
            values={"initial_traffic":initial,"traffic_max":traffic_max,"traffic_min":traffic_min,"traffic_per_100k_month":traffic_per,"admin_email":email,"bank_name":bank,"bank_holder":holder,"transfer_account":account,"transfer_note":transfer_note,"home_hero_title":hero_title,"home_hero_subtitle":hero_subtitle,"home_hero_width":hero_width,"home_hero_height":hero_height,"home_hero_title_size":hero_title_size,"home_hero_subtitle_size":hero_subtitle_size}
            for k,v in values.items():save_setting(k,v)
            st.success("設定已儲存")
    with tabs[5]:
        st.warning("Cloud 正式環境請使用外部 PostgreSQL 與持久化物件儲存；本功能提供管理員離線備份。")
        name,data=make_backup()
        st.download_button("備份到本地",data=data,file_name=name,mime="application/zip",use_container_width=True)
