import streamlit as st
import pandas as pd
from datetime import date,timedelta
from backend.services.appointment_service import mine,seller_pending,set_status,week_confirmed,delete_appointment
from backend.services.message_service import inbox,send_admin,set_message_status,quick_reply,delete_message,delete_messages
from backend.services.traffic_service import transactions,request_purchase,purchase_requests
from backend.services.admin_service import settings

def reservations():
    u=st.session_state.user;uid=u["id"];st.title("我的預約")

    st.subheader("買家提出給我的預約")
    pending_rows=[a for a in seller_pending(uid) if a["status"]=="等待確認"]
    show_all_pending=st.checkbox("顯示全部待確認預約",value=False,key="show_all_pending")
    shown_pending=pending_rows if show_all_pending else pending_rows[:10]
    if not shown_pending:st.info("目前沒有等待確認的買家預約。")
    for a in shown_pending:
        with st.container(border=True):
            st.write(f'#{a["id"]}｜{a["appointment_at"]}｜{a.get("listing_title","")}')
            st.caption(f'買家 ID：{a.get("other_user_id","")}｜{a.get("other_name","")}｜{a.get("other_email","")}｜{a.get("other_phone","")}')
            c1,c2=st.columns(2)
            if c1.button("確認",key=f'ok{a["id"]}',use_container_width=True):set_status(uid,a["id"],"已確認");st.rerun()
            if c2.button("拒絕",key=f'no{a["id"]}',use_container_width=True):set_status(uid,a["id"],"已拒絕");st.rerun()
    if len(pending_rows)>10 and not show_all_pending:st.caption(f"目前僅顯示最近 10 則，共 {len(pending_rows)} 則；勾選「顯示全部」可查看其餘紀錄。")

    st.divider();st.subheader("預約歷史紀錄")
    keyword=st.text_input("搜尋預約紀錄",placeholder="輸入對方使用者 ID、電話或 Gmail / Email",key="appointment_search")
    rows=mine(uid,keyword)
    focus=st.session_state.pop("appointment_focus",None)
    try:
        qp=st.query_params.get("appt_focus")
        if qp:
            focus=int(qp);del st.query_params["appt_focus"]
    except Exception:pass
    if focus:
        rows.sort(key=lambda r:r["id"]!=focus)
        st.success(f"已定位預約 #{focus}")
    show_all_history=st.checkbox("顯示全部預約歷史",value=False,key="show_all_appointment_history")
    shown=rows if show_all_history or focus else rows[:10]
    selected=[]
    if not shown:st.info("沒有符合條件的預約紀錄。")
    for a in shown:
        c0,c1=st.columns([0.08,0.92])
        if c0.checkbox("選取",key=f'appt_select_{a["id"]}',label_visibility="collapsed"):selected.append(a["id"])
        with c1:
            marker="📍 " if a["id"]==focus else ""
            with st.expander(f'{marker}#{a["id"]} [{a["status"]}] {a["appointment_at"]}｜{a.get("listing_title","")}',expanded=a["id"]==focus):
                st.caption(f'對方 ID：{a.get("other_user_id","")}｜姓名：{a.get("other_name","")}｜Email：{a.get("other_email","")}｜電話：{a.get("other_phone","")}')
                if a.get("note"):st.write(f'備註：{a["note"]}')
    if len(rows)>10 and not show_all_history and not focus:st.caption(f"目前僅顯示最近 10 則，共 {len(rows)} 則。")
    if selected:
        from backend.services.appointment_service import delete_appointments
        if st.button(f"批量刪除已選預約（{len(selected)}）",key="bulk_delete_appointments",use_container_width=True):
            ok,msg=delete_appointments(uid,selected);(st.success if ok else st.error)(msg)
            if ok:st.rerun()

    st.divider();st.subheader("預約日曆")
    target=st.date_input("Target 日期",value=date.today(),key="appointment_target_date")
    week_start,confirmed=week_confirmed(uid,target)
    st.caption(f"系統已鎖定當週：{week_start:%Y-%m-%d} ～ {(week_start+timedelta(days=6)):%Y-%m-%d}。紅色「已有預約」可直接定位該筆紀錄。")
    booked={}
    for a in confirmed:booked.setdefault((a["appointment_at"].date(),a["appointment_at"].hour),[]).append(a)
    day_names=["一","二","三","四","五","六","日"]
    html_rows=[]
    header="<tr><th>時間</th>"+"".join(f"<th>週{day_names[i]}<br>{(week_start+timedelta(days=i)):%m/%d}</th>" for i in range(7))+"</tr>"
    for hour in range(24):
        cells=[f"<th>{hour:02d}:00</th>"]
        for i in range(7):
            day=week_start+timedelta(days=i);items=booked.get((day,hour),[])
            if items:
                aid=items[0]["id"]
                cells.append(f'<td class="booked"><a href="?appt_focus={aid}">已有預約</a></td>')
            else:cells.append("<td>&nbsp;</td>")
        html_rows.append("<tr>"+"".join(cells)+"</tr>")
    st.markdown("""<style>
    .calendar-wrap{width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch;border:1px solid #245a9e;border-radius:12px}
    table.appt-grid{width:100%;min-width:760px;border-collapse:collapse;table-layout:fixed;background:#081525}
    .appt-grid th,.appt-grid td{border:1px solid #245a9e;text-align:center;padding:7px 4px;height:38px;white-space:nowrap;font-size:.82rem}
    .appt-grid th{background:#10294a;color:#dbeafe;position:sticky;top:0;z-index:1}
    .appt-grid th:first-child{width:68px}
    .appt-grid td.booked a{color:#ff4b4b!important;font-weight:800;text-decoration:none}
    @media(max-width:700px){table.appt-grid{min-width:680px}.appt-grid th,.appt-grid td{padding:6px 3px;font-size:.76rem}}
    </style>""",unsafe_allow_html=True)
    st.markdown('<div class="calendar-wrap"><table class="appt-grid"><thead>'+header+'</thead><tbody>'+''.join(html_rows)+'</tbody></table></div>',unsafe_allow_html=True)

def mailbox():
    uid=st.session_state.user["id"];st.title("信件區")
    clear_mid=st.session_state.pop("mail_reply_clear_mid",None)
    if clear_mid is not None:st.session_state.pop(f"mreply_{clear_mid}",None)
    notice=st.session_state.pop("mail_reply_notice",None)
    if notice:st.success(notice)
    c1,c2=st.columns([4,1]);keyword=c1.text_input("搜尋信件",placeholder="輸入寄件者使用者 ID、電話或 Gmail / Email",key="mail_search")
    if c2.button("重新整理",key="refresh_mailbox",use_container_width=True):st.rerun()
    rows=inbox(uid,keyword)
    if not rows:st.info("目前沒有符合條件的信件。");return
    selected=[]
    for m in rows:
        c0,c1=st.columns([0.08,0.92])
        if c0.checkbox("選取",key=f'mail_select_{m["id"]}',label_visibility="collapsed"):selected.append(m["id"])
        with c1:
            status=m.get("status","")
            status_color="#ef4444" if status=="未讀" else ("#22c55e" if status=="已讀" else "#eab308")
            st.markdown(f'<span style="color:{status_color};font-weight:800">● {status}</span>　#{m["id"]} {m["subject"]}｜{m["sender_name"]}',unsafe_allow_html=True)
            with st.expander("查看信件內容"):
                st.caption(f'使用者 ID：{m["sender_user_id"]}｜帳號名：{m["sender_name"]}｜信箱：{m["sender_email"]}｜電話：{m["sender_phone"]}')
                st.caption(f'寄送時間：{m["created_at"]}'+(f'｜商品 #{m["listing_id"]}' if m["listing_id"] else ""));st.write(m["body"])
                c1s,c2s=st.columns(2);new_status=c1s.selectbox("信件狀態",["未讀","已讀"],index=0 if m["status"]=="未讀" else 1,key=f'mstatus_{m["id"]}')
                if c2s.button("更新狀態",key=f'mstatus_btn_{m["id"]}',use_container_width=True):set_message_status(uid,m["id"],new_status);st.rerun()
                reply=st.text_area("快速回信",key=f'mreply_{m["id"]}',placeholder="輸入回覆內容")
                if st.button("送出回覆",key=f'mreply_btn_{m["id"]}',type="primary",use_container_width=True):
                    ok,msg=quick_reply(uid,m["id"],reply)
                    if ok:
                        st.session_state.mail_reply_clear_mid=m["id"]
                        st.session_state.mail_reply_notice="✅ 回覆已送出"
                        st.rerun()
                    else:st.error(msg)
    if selected:
        st.warning(f"已選擇 {len(selected)} 封信件。刪除後，被刪除方的信件狀態會改為「無送達紀錄」。")
        if st.button(f"批量刪除已選信件（{len(selected)}）",key="bulk_delete_mail",use_container_width=True):
            ok,msg=delete_messages(uid,selected);(st.success if ok else st.error)(msg)
            if ok:st.rerun()

def admin_contact():
    st.title("送信給管理員");cat=st.selectbox("類型",["帳戶問題","商品問題","預約問題","流量問題","付款問題","檢舉","建議","其他"]);sub=st.text_input("主旨");body=st.text_area("內容")
    if st.button("送信",use_container_width=True):
        if sub and body:send_admin(st.session_state.user["id"],cat,sub,body);st.success("已送交管理員信箱")
        else:st.error("主旨與內容不可為空")

def traffic():
    uid=st.session_state.user["id"];st.title("流量中心");s=settings()
    st.subheader("購買流量")
    st.info(f'銀行：{s.get("bank_name","尚未設定")}\n\n戶名：{s.get("bank_holder","尚未設定")}\n\n帳號：{s.get("transfer_account","尚未設定")}')
    if s.get("transfer_note"):st.caption(s["transfer_note"])
    st.caption("流量兌換：NT$1 = 1 流量；單次最低 NT$500。轉帳完成後提交申請，由管理員審核。")
    amt=st.number_input("轉帳金額",min_value=500,step=100);last5=st.text_input("匯款帳號末五碼",max_chars=5);note=st.text_area("備註")
    if st.button("送出購買申請",use_container_width=True):
        ok,msg=request_purchase(uid,int(amt),last5,note);st.success(msg) if ok else st.error(msg)
    st.subheader("購買申請狀態");requests=purchase_requests(uid)
    if requests:st.dataframe(pd.DataFrame(requests)[["id","amount","last5","status","created_at","note"]],use_container_width=True,hide_index=True)
    else:st.info("目前沒有流量購買申請。")
    st.divider()
    with st.expander("流量紀錄（最近 10 筆）",expanded=False):
        rows=transactions(uid,limit=10)
        if rows:st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
        else:st.info("目前沒有流量紀錄。")
