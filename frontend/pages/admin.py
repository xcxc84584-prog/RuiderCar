import streamlit as st
from backend.services.admin_service import settings,save_setting,save_settings,users_for_admin,blacklist_user,unblacklist_user,permanently_delete_user,bulk_blacklist_users,bulk_unblacklist_users,impersonate_user,pending_authorized_registrations,review_authorized_registration,admin_audit_logs
from backend.services.message_service import admin_messages,reply_admin,set_admin_message_status,delete_admin_messages,bulk_admin_message_status
from backend.services.traffic_service import pending,approve,reject
from backend.services.backup_service import make_backup
from backend.services.ip_service import admin_ip_rows,admin_set_ip_status,ip_history,export_ip_log_csv,delete_ip_log,delete_ip_logs_for_ip,clear_ip_logs,greylist_history_ips,delete_greylist_history,ip_diagnostics,client_ip_from_streamlit,admin_set_ip_request_limit,admin_delete_ip_records,publish_global_resource_limits
from backend.services.storage_service import admin_set_account_storage_limit

def render():
    if st.session_state.user.get("role")!="admin":st.error("沒有管理員權限");return
    st.title("管理員後台")
    tab_labels=["Dashboard","會員／黑名單","授權註冊審核","管理員信箱","流量審核","IP管理","系統設定","稽核紀錄","資料備份"]
    try:tabs=st.tabs(tab_labels,default=st.session_state.get("admin_active_tab","Dashboard"))
    except TypeError:tabs=st.tabs(tab_labels)
    with tabs[0]:
        st.info("管理員後台。")
    with tabs[1]:
        admin_uid=st.session_state.user["id"]
        users=users_for_admin(admin_uid)
        c1,c2=st.columns([3,1])
        keyword=c1.text_input("搜尋會員",placeholder="輸入會員 ID、姓名、Email 或手機",key="admin_user_search").strip().lower()
        show_deleted=c2.checkbox("顯示已註銷帳戶",value=False,key="admin_show_deleted")
        if not show_deleted:
            users=[u for u in users if not u["deleted"]]
        if keyword:
            users=[u for u in users if keyword in str(u["id"]).lower() or keyword in u["name"].lower() or keyword in u["email"].lower() or keyword in u["phone"].lower()]
        st.caption(f"搜尋結果：{len(users)} 位")
        if not users:st.info("沒有符合條件的會員。")
        selected_users=[]
        for u in users:
            if u["role"]!="admin" and st.checkbox(f'選取會員 #{u["id"]}',key=f'admin_select_user_{u["id"]}'):selected_users.append(u["id"])
            status="已註銷" if u["deleted"] else ("黑名單" if u["blacklisted"] else u.get("account_status","active"))
            with st.expander(f'#{u["id"]} [{status}] {u["name"]}｜{u["email"]}'):
                st.caption(f'電話：{u["phone"]}｜角色：{u["role"]}｜註冊類型：{u.get("registration_type","normal")}｜帳號狀態：{u.get("account_status","active")}｜流量：{u["traffic_balance"]}｜註冊：{u["created_at"]}')
                if not u["deleted"] and u["id"]!=st.session_state.user["id"]:
                    if st.button("強制登入／切換成此帳號",key=f'impersonate_{u["id"]}',width="stretch"):
                        ok,msg,target=impersonate_user(st.session_state.user["id"],u["id"])
                        if ok:
                            st.session_state.impersonator_admin=st.session_state.user.copy()
                            st.session_state.user=target
                            st.session_state.page="首頁"
                            st.rerun()
                        else:st.error(msg)
                if u["deleted"]:
                    st.info("此帳戶已註銷，僅保留歷史資料，不提供黑名單操作。")
                elif u["blacklisted"]:
                    st.error(f'黑名單原因：{u["blacklist_reason"]}')
                    st.caption(f'加入時間：{u["blacklisted_at"]}')
                    if st.button("解除黑名單",key=f'unblack_{u["id"]}',width="stretch"):
                        ok,msg=unblacklist_user(admin_uid,u["id"])
                        (st.success if ok else st.error)(msg)
                        if ok:st.rerun()
                elif u["role"]!="admin":
                    reason=st.text_input("加入黑名單原因",key=f'black_reason_{u["id"]}',placeholder="例如：詐騙疑慮、違反平台規則")
                    if st.button("加入黑名單",key=f'black_{u["id"]}',type="primary",width="stretch"):
                        ok,msg=blacklist_user(admin_uid,u["id"],reason)
                        (st.success if ok else st.error)(msg)
                        if ok:st.rerun()
                else:
                    st.info("管理員帳號不可加入黑名單。")
                if u["role"]!="admin":
                    st.divider()
                    st.error("危險操作：徹底刪除會移除此帳號及其平台關聯資料，無法復原。")
                    confirm=st.checkbox("我確認要永久刪除此帳號及相關資料",key=f'permadelete_confirm_{u["id"]}')
                    if st.button("徹底刪除帳號",key=f'permadelete_{u["id"]}',type="primary",width="stretch",disabled=not confirm):
                        ok,msg=permanently_delete_user(st.session_state.user["id"],u["id"])
                        (st.success if ok else st.error)(msg)
                        if ok:st.rerun()
        if selected_users:
            st.divider();st.subheader("批量會員操作")
            batch_reason=st.text_input("批量加入黑名單原因",key="bulk_blacklist_reason")
            b1,b2=st.columns(2)
            if b1.button(f"批量加入黑名單（{len(selected_users)}）",width="stretch"):
                ok,msg=bulk_blacklist_users(admin_uid,selected_users,batch_reason);(st.success if ok else st.error)(msg)
                if ok:st.rerun()
            if b2.button(f"批量解除黑名單（{len(selected_users)}）",width="stretch"):
                ok,msg=bulk_unblacklist_users(admin_uid,selected_users);(st.success if ok else st.error)(msg)
                if ok:st.rerun()
            bulk_delete_confirm=st.checkbox("我確認要永久刪除所有已選會員及其平台關聯資料",key="bulk_permadelete_confirm")
            if st.button(f"批量徹底刪除帳號（{len(selected_users)}）",disabled=not bulk_delete_confirm,width="stretch"):
                done=0
                for target_uid in selected_users:
                    ok,_=permanently_delete_user(st.session_state.user["id"],target_uid);done+=1 if ok else 0
                st.success(f"已永久刪除 {done} 位會員");st.rerun()
    with tabs[2]:
        admin_uid=st.session_state.user["id"]
        rows=pending_authorized_registrations(admin_uid)
        if not rows:st.info("目前沒有等待批准的授權註冊。")
        for r in rows:
            with st.container(border=True):
                st.write(f'#{r["id"]}｜{r["name"]}｜{r["email"]}')
                st.caption(f'電話：{r["phone"]}｜申請時間：{r["created_at"]}')
                c1,c2=st.columns(2)
                if c1.button("批准註冊",key=f'authreg_ok_{r["id"]}',type="primary",width="stretch"):
                    ok,msg=review_authorized_registration(admin_uid,r["id"],True);(st.success if ok else st.error)(msg)
                    if ok:st.rerun()
                if c2.button("拒絕註冊",key=f'authreg_no_{r["id"]}',width="stretch"):
                    ok,msg=review_authorized_registration(admin_uid,r["id"],False);(st.success if ok else st.error)(msg)
                    if ok:st.rerun()
    with tabs[3]:
        notice=st.session_state.pop("admin_reply_notice",None)
        if notice:st.success(notice)
        admin_uid=st.session_state.user["id"]
        rows=admin_messages(admin_uid)
        if not rows:st.info("目前沒有管理員信件。")
        selected_admin_messages=[]
        for m in rows:
            if st.checkbox(f'選取通知 #{m["id"]}',key=f'admin_msg_select_{m["id"]}'):selected_admin_messages.append(m["id"])
            with st.expander(f'#{m["id"]} [{m["status"]}] {m["subject"]}｜{m["user_name"]}'):
                st.caption(f'帳號名：{m["user_name"]}｜信箱：{m["user_email"]}｜電話：{m["user_phone"]}')
                st.caption(f'類型：{m["category"]}｜送出時間：{m["created_at"]}')
                st.write(m["body"])
                statuses=["未讀","已讀","處理中","已回覆","已關閉"]
                idx=statuses.index(m["status"]) if m["status"] in statuses else 0
                c1,c2=st.columns(2)
                ns=c1.selectbox("狀態",statuses,index=idx,key=f'ams_{m["id"]}')
                if c2.button("更新狀態",key=f'amsb_{m["id"]}',width="stretch"):
                    set_admin_message_status(admin_uid,m["id"],ns);st.rerun()
                r=st.text_area("快速回信",value=m["reply"],key=f'r{m["id"]}')
                if st.button("回覆並標記已回覆",key=f'rr{m["id"]}',type="primary",width="stretch"):
                    if reply_admin(admin_uid,m["id"],r):
                        st.session_state.admin_reply_notice="✅ 回覆已送出";st.rerun()
                    else:st.error("回覆內容不可為空或沒有管理員權限")
        if selected_admin_messages:
            st.divider();st.subheader("批量通知操作")
            new_bulk_status=st.selectbox("批量狀態",["未讀","已讀","處理中","已回覆","已關閉"],key="bulk_admin_message_status")
            b1,b2=st.columns(2)
            if b1.button(f"批量更新狀態（{len(selected_admin_messages)}）",width="stretch"):
                ok,msg=bulk_admin_message_status(admin_uid,selected_admin_messages,new_bulk_status);(st.success if ok else st.error)(msg)
                if ok:st.rerun()
            if b2.button(f"批量刪除通知（{len(selected_admin_messages)}）",width="stretch"):
                ok,msg=delete_admin_messages(admin_uid,selected_admin_messages);(st.success if ok else st.error)(msg)
                if ok:st.rerun()
    with tabs[4]:
        admin_uid=st.session_state.user["id"]
        rows=pending(admin_uid)
        if not rows:st.info("目前沒有等待審核的流量購買申請。")
        selected_traffic=[]
        for r in rows:
            if st.checkbox(f'選取申請 #{r["id"]}',key=f'traffic_select_{r["id"]}'):selected_traffic.append(r["id"])
            with st.container(border=True):
                st.write(f'申請 #{r["id"]}｜會員 {r["user_id"]}｜NT$ {r["amount"]}｜末五碼 {r["last5"]}')
                st.caption(f'申請時間：{r["created_at"]}')
                if r.get("note"):st.write(f'備註：{r["note"]}')
                c1,c2=st.columns(2)
                if c1.button("批准",key=f'ap{r["id"]}',type="primary",width="stretch"):
                    ok,msg=approve(admin_uid,r["id"])
                    (st.success if ok else st.error)(msg)
                    if ok:st.rerun()
                if c2.button("拒絕",key=f'rj{r["id"]}',width="stretch"):
                    ok,msg=reject(admin_uid,r["id"])
                    (st.success if ok else st.error)(msg)
                    if ok:st.rerun()
        if selected_traffic:
            st.divider();st.subheader("批量流量審核")
            b1,b2=st.columns(2)
            if b1.button(f"批量批准（{len(selected_traffic)}）",width="stretch"):
                done=0
                for rid in selected_traffic:
                    ok,_=approve(admin_uid,rid);done+=1 if ok else 0
                st.success(f"已批准 {done} 筆申請");st.rerun()
            if b2.button(f"批量拒絕（{len(selected_traffic)}）",width="stretch"):
                done=0
                for rid in selected_traffic:
                    ok,_=reject(admin_uid,rid);done+=1 if ok else 0
                st.success(f"已拒絕 {done} 筆申請");st.rerun()
    with tabs[5]:
        st.subheader("IP 管理")
        ip_notice=st.session_state.pop("ip_admin_notice",None)
        if ip_notice:st.success(ip_notice)
        diag=ip_diagnostics(client_ip_from_streamlit(st))
        if diag["security_usable"]:st.success(f'目前 Client IP：{diag["ip"]}｜IP 安全控制可運作')
        else:st.warning(f'目前 Client IP：{diag["ip"]}｜安全降級模式：{diag["reason"]}')
        st.caption("Streamlit Cloud 若僅提供 127.0.0.1，RuiderCar 會以 IP + Account/Guest Identity 區分應用層用戶；此識別不等同真實 Public IP。")
        c1,c2=st.columns([3,1])
        ip_keyword=c1.text_input("搜尋 IP",key="admin_ip_search").strip()
        ip_status=c2.selectbox("狀態",["all","normal","whitelist","greylist","blacklist"],key="admin_ip_status")
        rows=admin_ip_rows(st.session_state.user["id"],ip_keyword,ip_status)
        st.caption(f"目前列出 {len(rows)} 個 IP。請求速度為 RuiderCar 應用層 requests/min，並非實體網路 Mbps。")
        selected_set=set(st.session_state.get("admin_ip_selected",[]))
        visible_ips=[r["ip"] for r in rows]
        sa1,sa2,sa3=st.columns([1,1,2])
        if sa1.button("全選目前搜尋結果",disabled=not rows,width="stretch",key="admin_ip_select_all_btn"):
            selected_set.update(visible_ips);st.session_state.admin_ip_selected=list(selected_set)
            for ip in visible_ips:st.session_state[f'ip_select_{ip}']=True
            st.rerun()
        if sa2.button("取消目前選取",disabled=not rows,width="stretch",key="admin_ip_clear_visible_btn"):
            selected_set.difference_update(visible_ips);st.session_state.admin_ip_selected=list(selected_set)
            for ip in visible_ips:st.session_state[f'ip_select_{ip}']=False
            st.rerun()
        sa3.caption(f"目前已選取 {len(selected_set)} 個 Identity")
        selected_ip_records=[]
        for r in rows:
            key=f'ip_select_{r["ip"]}'
            if key not in st.session_state:st.session_state[key]=r["ip"] in selected_set
            checked=st.checkbox(f'選取 {r["ip"]}',key=key)
            if checked:selected_set.add(r["ip"]);selected_ip_records.append(r["ip"])
            else:selected_set.discard(r["ip"])
            st.session_state.admin_ip_selected=list(selected_set)
            with st.expander(f'{r["ip"]}｜{r["status"]}｜{r["requests/min"]} req/min｜最後 {r["last_seen"]}'):
                st.write(f'首次訪問：{r["first_seen"]}')
                st.write(f'累計請求：{r["request_count"]}｜最高：{r["peak"]} requests/min')
                if r["reason"]:st.warning(f'原因：{r["reason"]}')
                if r["greylisted_until"]:st.caption(f'灰名單至：{r["greylisted_until"]}')
                global_limit=int(settings().get("ip_request_limit_per_minute","180"))
                if r.get("resource_exempt"):
                    label="Administrator" if r.get("admin_exempt") else "Whitelist"
                    st.success(f"🛡️ {label}－流量限制、資料量限制與 Active Queue 豁免；Request Rate / LOG 仍正常記錄。")
                    st.info(f'流量：{r.get("requests/min",0)} req/min / Unlimited｜資料量：{r.get("storage_used_mb",0):.2f} MB / Unlimited')
                else:
                    st.info(f'目前流量上限：{global_limit} requests/min（全站統一設定）')
                    if r.get("account_id"):
                        global_storage=int(settings().get("default_storage_limit_mb","100"))
                        st.info(f'資料量：{r.get("storage_used_mb",0):.2f} / {global_storage} MB（全站統一設定）')
                a,b,c=st.columns(3)
                if a.button("加入黑名單",key=f'ip_black_{r["ip"]}',width="stretch"):
                    bar=st.progress(35,text="正在更新 IP 狀態…");ok,msg=admin_set_ip_status(st.session_state.user["id"],r["ip"],"blacklist");bar.progress(100,text="更新完成");st.session_state.ip_admin_notice=msg;st.session_state.admin_active_tab="IP管理";st.rerun()
                if b.button("加入白名單",key=f'ip_white_{r["ip"]}',width="stretch"):
                    bar=st.progress(35,text="正在更新 IP 狀態…");ok,msg=admin_set_ip_status(st.session_state.user["id"],r["ip"],"whitelist");bar.progress(100,text="更新完成");st.session_state.ip_admin_notice=msg;st.session_state.admin_active_tab="IP管理";st.rerun()
                if c.button("恢復一般",key=f'ip_normal_{r["ip"]}',width="stretch"):
                    bar=st.progress(35,text="正在更新 IP 狀態…");ok,msg=admin_set_ip_status(st.session_state.user["id"],r["ip"],"normal");bar.progress(100,text="更新完成");st.session_state.ip_admin_notice=msg;st.session_state.admin_active_tab="IP管理";st.rerun()
                load_hist=st.toggle("載入完整活動歷史",value=False,key=f'load_ip_history_{r["ip"]}')
                if load_hist:
                    with st.spinner("載入活動歷史…"):
                        hist=ip_history(st.session_state.user["id"],r["ip"],100)
                    if hist:
                        st.dataframe(hist,width="stretch",hide_index=True)
                        ids=[x["ID"] for x in hist if x["事件"]!="GREYLIST"]
                        if ids:
                            selected=st.selectbox("選擇要刪除的一般 LOG ID",ids,key=f'log_delete_select_{r["ip"]}')
                            if st.button("刪除選取 LOG",key=f'log_delete_{r["ip"]}'):
                                ok,msg=delete_ip_log(st.session_state.user["id"],selected);(st.success if ok else st.error)(msg);st.session_state.admin_active_tab="IP管理";st.rerun()
                        if st.checkbox("確認刪除此 IP 的一般 LOG",key=f'confirm_ip_logs_{r["ip"]}'):
                            if st.button("刪除此 IP 一般 LOG",key=f'delete_ip_logs_{r["ip"]}',type="primary"):
                                ok,msg=delete_ip_logs_for_ip(st.session_state.user["id"],r["ip"]);(st.success if ok else st.error)(msg);st.session_state.admin_active_tab="IP管理";st.rerun()
                    else:st.caption("此 Identity 沒有活動歷史。")
        if selected_ip_records:
            st.divider();st.subheader("批量 IP Identity 操作")
            st.caption(f"已選取 {len(selected_ip_records)} 個 Identity。刪除 Identity 時會刪除其一般 LOG，但保留灰名單歷史。")
            confirm_bulk=st.checkbox("我確認要批量刪除選取的 IP Identity",key="confirm_bulk_delete_ips")
            if st.button(f"批量刪除（{len(selected_ip_records)}）",type="primary",width="stretch",disabled=not confirm_bulk,key="bulk_delete_ip_records"):
                bar=st.progress(10,text="正在準備批量刪除…")
                bar.progress(45,text=f"正在處理 {len(selected_ip_records)} 個 IP Identity…")
                ok,msg,_=admin_delete_ip_records(st.session_state.user["id"],selected_ip_records)
                bar.progress(100,text="處理完成")
                st.session_state.ip_admin_notice=msg
                if ok:
                    deleted=set(selected_ip_records);st.session_state.admin_ip_selected=[x for x in st.session_state.get("admin_ip_selected",[]) if x not in deleted]
                    for ip in deleted:st.session_state.pop(f"ip_select_{ip}",None)
                st.session_state.admin_active_tab="IP管理"
                st.rerun()
        st.divider();st.subheader("灰名單歷史")
        st.caption("灰名單歷史不受一般 IP LOG 保存天數影響，只會在管理員主動刪除時移除。非展開狀態只顯示最近 1 筆。")
        grey=greylist_history_ips(st.session_state.user["id"])
        if not grey:st.info("目前沒有灰名單歷史。")
        for g in grey:
            latest=g["latest"]
            st.markdown(f'**{g["ip"]}**｜累計 {g["count"]} 次｜最近：{latest["time"]}｜{latest["detail"]}')
            with st.expander("展開全部灰名單歷史"):
                st.dataframe(g["history"],width="stretch",hide_index=True)
                gids=[x["id"] for x in g["history"]]
                gid=st.selectbox("選擇灰名單歷史 ID",gids,key=f'grey_id_{g["ip"]}')
                x1,x2=st.columns(2)
                if x1.button("刪除選取灰名單歷史",key=f'grey_del_one_{g["ip"]}',width="stretch"):
                    ok,msg=delete_greylist_history(st.session_state.user["id"],log_id=gid);(st.success if ok else st.error)(msg);st.session_state.admin_active_tab="IP管理";st.rerun()
                if x2.checkbox("確認刪除此 IP 全部灰名單歷史",key=f'grey_confirm_all_{g["ip"]}'):
                    if st.button("刪除此 IP 全部灰名單歷史",key=f'grey_del_all_{g["ip"]}',type="primary",width="stretch"):
                        ok,msg=delete_greylist_history(st.session_state.user["id"],ip=g["ip"]);(st.success if ok else st.error)(msg);st.session_state.admin_active_tab="IP管理";st.rerun()
        st.divider()
        name,data=export_ip_log_csv(st.session_state.user["id"])
        st.download_button("下載 IP LOG (.csv)",data=data,file_name=name,mime="text/csv",width="stretch")
        if st.checkbox("我確認要清除全部一般 IP LOG（不含灰名單歷史）",key="confirm_clear_ip_logs"):
            if st.button("清空全部一般 IP LOG",type="primary",width="stretch"):
                ok,msg=clear_ip_logs(st.session_state.user["id"]);(st.success if ok else st.error)(msg);st.session_state.admin_active_tab="IP管理";st.rerun()
    with tabs[6]:
        notice=st.session_state.pop("system_settings_notice",None)
        if notice:st.success(notice)
        s=settings()
        st.subheader("IP / 資源管理")
        ic1,ic2,ic3=st.columns(3)
        ip_request_limit=ic1.number_input("每 IP 最大請求數／分鐘",min_value=10,max_value=100000,value=int(s.get("ip_request_limit_per_minute","180")),step=10)
        active_ip_limit=ic2.number_input("同時 Active IP 上限",min_value=1,max_value=100000,value=int(s.get("active_ip_limit","50")),step=1)
        ip_log_retention_days=ic3.number_input("IP LOG 保存天數",min_value=1,max_value=3650,value=int(s.get("ip_log_retention_days","7")),step=1)
        default_storage_limit_mb=st.number_input("每 Account 預設資料量限制（MB）",min_value=1,max_value=102400,value=int(s.get("default_storage_limit_mb","100")),step=10)
        st.caption("Active IP：最近 5 分鐘內有活動的 IP。超過請求門檻會進入灰名單 30 分鐘並撤銷該 IP 的登入 Session；白名單與 Administrator 豁免流量限制、資料量限制與排隊；其餘一般帳號統一套用最新全站設定。")
        st.divider()
        account_limit=st.number_input("平台帳號數量上限",min_value=1,max_value=100000,value=int(s.get("account_limit","500")),step=10)
        st.caption("目前預設 500。此上限只限制一般註冊；授權註冊不受此上限影響，但必須經管理員批准後才能登入。")
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
        st.divider()
        st.subheader("輔助與說明設定")
        help_changelog=st.text_area("更新日誌（支援 Markdown）",value=s.get("help_changelog",""),height=220)
        help_guide=st.text_area("操作說明（支援 Markdown）",value=s.get("help_guide",""),height=260)
        if st.button("儲存系統設定",width="stretch"):
            values={"ip_request_limit_per_minute":ip_request_limit,"active_ip_limit":active_ip_limit,"ip_log_retention_days":ip_log_retention_days,"default_storage_limit_mb":default_storage_limit_mb,"account_limit":account_limit,"initial_traffic":initial,"traffic_max":traffic_max,"traffic_min":traffic_min,"traffic_per_100k_month":traffic_per,"admin_email":email,"bank_name":bank,"bank_holder":holder,"transfer_account":account,"transfer_note":transfer_note,"home_hero_title":hero_title,"home_hero_subtitle":hero_subtitle,"home_hero_width":hero_width,"home_hero_height":hero_height,"home_hero_title_size":hero_title_size,"home_hero_subtitle_size":hero_subtitle_size,"help_changelog":help_changelog,"help_guide":help_guide}
            ok,msg=save_settings(st.session_state.user["id"],values)
            (st.success if ok else st.error)(msg)
            if ok:
                pub_ok,pub_msg=publish_global_resource_limits(st.session_state.user["id"])
                st.session_state.system_settings_notice=("✅ 系統設定已成功寫入資料庫。"+pub_msg) if pub_ok else ("⚠️ 系統設定已儲存，但資源限制發佈失敗："+pub_msg)
                st.session_state.admin_active_tab="系統設定"
                st.rerun()
    with tabs[7]:
        logs=admin_audit_logs(st.session_state.user["id"])
        if logs:st.dataframe(logs,width="stretch",hide_index=True)
        else:st.info("目前沒有管理員稽核紀錄。")
    with tabs[8]:
        st.warning("Cloud 正式環境請使用外部 PostgreSQL 與持久化物件儲存；本功能提供管理員離線備份。")
        name,data=make_backup(st.session_state.user["id"])
        st.download_button("備份到本地",data=data,file_name=name,mime="application/zip",width="stretch")
