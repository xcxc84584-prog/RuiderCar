import streamlit as st
import pandas as pd
from datetime import date,timedelta
from backend.services.appointment_service import mine,seller_pending,set_status,week_confirmed,delete_appointment
from backend.services.message_service import inbox,send_admin,set_message_status,quick_reply,delete_message
from backend.services.traffic_service import transactions,request_purchase,purchase_requests
from backend.services.admin_service import settings

def reservations():
    u=st.session_state.user;uid=u["id"];st.title("我的預約")
    st.subheader("預約日曆")
    target=st.date_input("Target 日期",value=date.today(),key="appointment_target_date")
    week_start,confirmed=week_confirmed(uid,target)
    st.caption(f"系統已鎖定當週：{week_start:%Y-%m-%d} ～ {(week_start+timedelta(days=6)):%Y-%m-%d}。紅色『已有預約』可直接定位該筆紀錄。")
    booked={}
    for a in confirmed:booked.setdefault((a["appointment_at"].date(),a["appointment_at"].hour),[]).append(a)
    headers=st.columns([0.55]+[1]*7)
    headers[0].markdown("**時間**")
    for i in range(7):headers[i+1].markdown(f"**{(week_start+timedelta(days=i)):%m/%d}**")
    for hour in range(24):
        cols=st.columns([0.55]+[1]*7);cols[0].markdown(f"`{hour:02d}:00`")
        for i in range(7):
            day=week_start+timedelta(days=i);items=booked.get((day,hour),[])
            if items:
                aid=items[0]["id"]
                if cols[i+1].button("🔴 已有預約",key=f"cal_{day}_{hour}",help=f"預約 #{aid}",use_container_width=True):
                    st.session_state.appointment_focus=aid
            else:cols[i+1].write("")
    st.divider();st.subheader("預約歷史紀錄")
    keyword=st.text_input("搜尋預約紀錄",placeholder="輸入對方使用者 ID、電話或 Gmail / Email",key="appointment_search")
    rows=mine(uid,keyword)
    focus=st.session_state.pop("appointment_focus",None)
    if focus:
        rows.sort(key=lambda r:r["id"]!=focus)
        st.success(f"已定位預約 #{focus}")
    if not rows:st.info("沒有符合條件的預約紀錄。")
    for a in rows:
        marker="📍 " if a["id"]==focus else ""
        with st.expander(f'{marker}#{a["id"]} [{a["status"]}] {a["appointment_at"]}｜{a.get("listing_title","")}',expanded=a["id"]==focus):
            st.caption(f'對方 ID：{a.get("other_user_id","")}｜姓名：{a.get("other_name","")}｜Email：{a.get("other_email","")}｜電話：{a.get("other_phone","")}')
            if a.get("note"):st.write(f'備註：{a["note"]}')
            confirm=st.checkbox("確認刪除此預約歷史紀錄",key=f'delappt_confirm_{a["id"]}')
            if st.button("刪除預約紀錄",key=f'delappt_{a["id"]}',disabled=not confirm,use_container_width=True):
                ok,msg=delete_appointment(uid,a["id"]);(st.success if ok else st.error)(msg)
                if ok:st.rerun()
    st.divider();st.subheader("買家提出給我的預約")
    for a in seller_pending(uid):
        if a["status"]!="等待確認":continue
        st.write(f'#{a["id"]}｜{a["appointment_at"]}｜{a["status"]}')
        c1,c2=st.columns(2)
        if c1.button("確認",key=f'ok{a["id"]}'):set_status(uid,a["id"],"已確認");st.rerun()
        if c2.button("拒絕",key=f'no{a["id"]}'):set_status(uid,a["id"],"已拒絕");st.rerun()

def mailbox():
    uid=st.session_state.user["id"];st.title("信件區")
    c1,c2=st.columns([4,1]);keyword=c1.text_input("搜尋信件",placeholder="輸入寄件者使用者 ID、電話或 Gmail / Email",key="mail_search")
    if c2.button("重新整理",key="refresh_mailbox",use_container_width=True):st.rerun()
    rows=inbox(uid,keyword)
    if not rows:st.info("目前沒有符合條件的信件。");return
    for m in rows:
        label=f'#{m["id"]} [{m["status"]}] {m["subject"]}｜{m["sender_name"]}'
        with st.expander(label):
            st.caption(f'使用者 ID：{m["sender_user_id"]}｜帳號名：{m["sender_name"]}｜信箱：{m["sender_email"]}｜電話：{m["sender_phone"]}')
            st.caption(f'寄送時間：{m["created_at"]}'+(f'｜商品 #{m["listing_id"]}' if m["listing_id"] else ""));st.write(m["body"])
            c1,c2=st.columns(2);new_status=c1.selectbox("信件狀態",["未讀","已讀"],index=0 if m["status"]=="未讀" else 1,key=f'mstatus_{m["id"]}')
            if c2.button("更新狀態",key=f'mstatus_btn_{m["id"]}',use_container_width=True):set_message_status(uid,m["id"],new_status);st.rerun()
            reply=st.text_area("快速回信",key=f'mreply_{m["id"]}',placeholder="輸入回覆內容")
            if st.button("送出回覆",key=f'mreply_btn_{m["id"]}',type="primary",use_container_width=True):
                ok,msg=quick_reply(uid,m["id"],reply);(st.success if ok else st.error)(msg)
                if ok:st.rerun()
            st.divider();confirm=st.checkbox("確認刪除此信件",key=f'delmail_confirm_{m["id"]}')
            if st.button("刪除信件",key=f'delmail_{m["id"]}',disabled=not confirm,use_container_width=True):
                ok,msg=delete_message(uid,m["id"]);(st.success if ok else st.error)(msg)
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
