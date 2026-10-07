import streamlit as st
import pandas as pd
from backend.services.appointment_service import mine,seller_pending,set_status
from backend.services.message_service import inbox,send_admin,set_message_status,quick_reply
from backend.services.traffic_service import transactions,request_purchase,purchase_requests
from backend.services.admin_service import settings

def reservations():
    u=st.session_state.user;st.title("我的預約")
    data=mine(u["id"]);st.dataframe(pd.DataFrame(data),use_container_width=True,hide_index=True)
    st.subheader("買家提出給我的預約")
    for a in seller_pending(u["id"]):
        st.write(f'#{a["id"]}｜{a["appointment_at"]}｜{a["status"]}')
        c1,c2=st.columns(2)
        if c1.button("確認",key=f'ok{a["id"]}'):set_status(u["id"],a["id"],"已確認");st.rerun()
        if c2.button("拒絕",key=f'no{a["id"]}'):set_status(u["id"],a["id"],"已拒絕");st.rerun()

def mailbox():
    uid=st.session_state.user["id"];st.title("信件區")
    rows=inbox(uid)
    if not rows:
        st.info("目前沒有信件。");return
    for m in rows:
        label=f'#{m["id"]} [{m["status"]}] {m["subject"]}｜{m["sender_name"]}'
        with st.expander(label):
            st.caption(f'帳號名：{m["sender_name"]}｜信箱：{m["sender_email"]}｜電話：{m["sender_phone"]}')
            st.caption(f'寄送時間：{m["created_at"]}'+(f'｜商品 #{m["listing_id"]}' if m["listing_id"] else ""))
            st.write(m["body"])
            c1,c2=st.columns(2)
            new_status=c1.selectbox("信件狀態",["未讀","已讀"],index=0 if m["status"]=="未讀" else 1,key=f'mstatus_{m["id"]}')
            if c2.button("更新狀態",key=f'mstatus_btn_{m["id"]}',use_container_width=True):
                set_message_status(uid,m["id"],new_status);st.rerun()
            reply=st.text_area("快速回信",key=f'mreply_{m["id"]}',placeholder="輸入回覆內容")
            if st.button("送出回覆",key=f'mreply_btn_{m["id"]}',type="primary",use_container_width=True):
                ok,msg=quick_reply(uid,m["id"],reply)
                (st.success if ok else st.error)(msg)
                if ok:st.rerun()

def admin_contact():
    st.title("送信給管理員")
    cat=st.selectbox("類型",["帳戶問題","商品問題","預約問題","流量問題","付款問題","檢舉","建議","其他"])
    sub=st.text_input("主旨");body=st.text_area("內容")
    if st.button("送信",use_container_width=True):
        if sub and body:send_admin(st.session_state.user["id"],cat,sub,body);st.success("已送交管理員信箱")
        else:st.error("主旨與內容不可為空")

def traffic():
    uid=st.session_state.user["id"];st.title("流量中心")
    s=settings()
    st.subheader("管理員收款帳戶")
    st.info(
        f'銀行：{s.get("bank_name","尚未設定")}\n\n'
        f'戶名：{s.get("bank_holder","尚未設定")}\n\n'
        f'帳號：{s.get("transfer_account","尚未設定")}'
    )
    if s.get("transfer_note"):st.caption(s["transfer_note"])
    st.caption("流量兌換：NT$1 = 1 流量；單次最低 NT$500。轉帳完成後請提交下方申請，由管理員審核。")
    st.subheader("流量紀錄")
    st.dataframe(pd.DataFrame(transactions(uid)),use_container_width=True,hide_index=True)
    st.subheader("購買申請狀態")
    requests=purchase_requests(uid)
    if requests:
        st.dataframe(pd.DataFrame(requests)[["id","amount","last5","status","created_at","note"]],use_container_width=True,hide_index=True)
    else:
        st.info("目前沒有流量購買申請。")
    st.subheader("購買流量")
    amt=st.number_input("轉帳金額",min_value=500,step=100)
    last5=st.text_input("匯款帳號末五碼",max_chars=5)
    note=st.text_area("備註")
    if st.button("送出購買申請",use_container_width=True):
        ok,msg=request_purchase(uid,int(amt),last5,note);st.success(msg) if ok else st.error(msg)
