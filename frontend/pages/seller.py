import streamlit as st
from backend.services.listing_service import create_draft,user_listings,update_draft,publish,publication_cost,delete_draft,unlist_refund_preview,unlist
from backend.services.image_service import add_uploaded_images,delete_image,move_image,image_source
def _data(prefix="",values=None,product_type_override=None,show_type=True):
    v=values or {}
    types=["車輛商品","常規商品"];type0="常規商品" if v.get("product_type")=="general" else "車輛商品"
    if product_type_override is not None:
        product_type=product_type_override
    elif show_type:
        type_label=st.selectbox("商品類型",types,index=types.index(type0),key=f"{prefix}product_type")
        product_type="general" if type_label=="常規商品" else "vehicle"
    else:
        product_type=v.get("product_type","vehicle")
    title=st.text_input("商品名稱",value=v.get("title",""),key=f"{prefix}title")
    price=st.number_input("價格",min_value=0,step=1000,value=int(v.get("price",0)),key=f"{prefix}price")
    summary=st.text_input("商品卡簡述",value=v.get("summary",""),key=f"{prefix}summary")
    description=st.text_area("詳細說明",value=v.get("description",""),key=f"{prefix}description")
    brand=model=color="";year=2026;mileage=0;fuel="";trans="";body=""
    if product_type=="vehicle":
        c1,c2,c3=st.columns(3)
        brand=c1.text_input("廠牌",value=v.get("brand",""),key=f"{prefix}brand")
        model=c2.text_input("車型",value=v.get("model",""),key=f"{prefix}model")
        year=c3.number_input("年式",2000,2035,int(v.get("year",2022)),key=f"{prefix}year")
        c1,c2,c3=st.columns(3)
        mileage=c1.number_input("里程 km",0,10000000,int(v.get("mileage",0)),key=f"{prefix}mileage")
        fuels=["汽油","柴油","油電混合","插電式油電","純電動","其他"];fuel0=v.get("fuel","汽油");fuel=c2.selectbox("能源",fuels,index=fuels.index(fuel0) if fuel0 in fuels else 0,key=f"{prefix}fuel")
        transs=["自排","手排","CVT","DCT","手自排","其他"];trans0=v.get("transmission","自排");trans=c3.selectbox("變速",transs,index=transs.index(trans0) if trans0 in transs else 0,key=f"{prefix}trans")
        bodies=["轎車","掀背車","旅行車","休旅車","跨界休旅","跑車","敞篷車","MPV","廂型車","皮卡","其他"];body0=v.get("body_type","轎車")
        c1,c2=st.columns(2);body=c1.selectbox("車身型式",bodies,index=bodies.index(body0) if body0 in bodies else 0,key=f"{prefix}body");color=c2.text_input("顏色",value=v.get("color",""),key=f"{prefix}color")
    location=st.text_input("所在地",value=v.get("location",""),key=f"{prefix}location")
    meeting=st.text_input("交易／看貨地址",value=v.get("meeting_address",""),key=f"{prefix}meeting")
    delivery=st.text_input("預計交付時間",value=v.get("delivery_time","成交後 3 日內"),key=f"{prefix}delivery")
    opts=["現金","銀行轉帳","貸款","其他"];old=[x for x in str(v.get("payment_method","")).split("／") if x in opts]
    payment=st.multiselect("付款方式",opts,default=old,key=f"{prefix}payment")
    loan=st.checkbox("接受貸款",value=bool(v.get("accepts_loan",False)),key=f"{prefix}loan") if product_type=="vehicle" else False
    month_opts=[1,2,3,6,12];m=int(v.get("months",1));months=st.selectbox("上架時長（月）",month_opts,index=month_opts.index(m) if m in month_opts else 0,key=f"{prefix}months")
    return dict(product_type=product_type,title=title,price=int(price),summary=summary,description=description,brand=brand,model=model,year=int(year),mileage=int(mileage),fuel=fuel,transmission=trans,location=location,body_type=body,color=color,meeting_address=meeting,delivery_time=delivery,payment_method="／".join(payment),accepts_loan=loan,months=months)
def render():
    uid=st.session_state.user["id"];st.title("賣出／商品管理")
    flash=st.session_state.pop("seller_flash",None)
    if flash:
        (st.success if flash[0]=="success" else st.error)(flash[1])
    if "seller_section" not in st.session_state:
        st.session_state.seller_section="建立商品"
    section=st.radio("商品管理",["建立商品","我的商品"],horizontal=True,key="seller_section",label_visibility="collapsed")
    if section=="建立商品":
        new_type_label=st.selectbox("商品類型",["車輛商品","常規商品"],key="new_product_type_live")
        new_product_type="general" if new_type_label=="常規商品" else "vehicle"
        if new_product_type=="general":st.caption("常規商品模式：車輛專屬欄位已隱藏。")
        with st.form("new_listing"):
            data=_data("new_",product_type_override=new_product_type,show_type=False)
            submit=st.form_submit_button("儲存草稿",use_container_width=True)
            if submit:
                lid,msg=create_draft(uid,data)
                if lid:st.success(f"草稿 #{lid} 已建立")
                else:st.error(msg)
    if section=="我的商品":
        xs=user_listings(uid)
        show_images=st.checkbox("顯示圖片",value=True,key="seller_show_images")
        if not xs:st.info("目前沒有商品。")
        for x in xs:
            imgs=x.get("images") or []
            status_label={"draft":"草稿","active":"已上架","closed":"已下架"}.get(x["status"],x["status"])
            with st.container(border=True):
                if x["status"]=="active":st.success("🟢 已上架")
                elif x["status"]=="draft":st.warning("🟡 草稿／未上架")
                else:st.info(f"⚪ {status_label}")
                if show_images:
                    cimg,cinfo=st.columns([1,2])
                    with cimg:
                        if imgs:
                            source=image_source(imgs[0])
                            if source is not None:st.image(source,use_container_width=True)
                            else:st.caption("封面圖片暫時無法顯示")
                        else:
                            st.caption("尚未上傳封面圖片")
                    with cinfo:
                        st.markdown(f'### {x["title"]}')
                        st.markdown(f'**NT$ {x["price"]:,}**')
                        type_label="車輛商品" if x.get("product_type","vehicle")=="vehicle" else "常規商品"
                        st.caption(f'商品 #{x["id"]}｜{type_label}｜狀態：{status_label}｜已扣流量：{x["traffic_cost"]}')
                        if x.get("product_type","vehicle")=="vehicle":st.write(f'里程：**{x["mileage"]:,} km**')
                        if x.get("summary"):st.write(x["summary"])
                        st.caption(f'賣家：{x.get("seller_name","")}｜{x.get("seller_email","")}｜{x.get("seller_phone","")}')
                        if x["status"]=="active" and x.get("expires_at"):st.caption(f'預計到期：{x["expires_at"]}')
                else:
                    type_label="車輛商品" if x.get("product_type","vehicle")=="vehicle" else "常規商品"
                    st.markdown(f'### {x["title"]}　　NT$ {x["price"]:,}')
                    st.caption(f'商品 #{x["id"]}｜{type_label}｜狀態：{status_label}｜已扣流量：{x["traffic_cost"]}')
                    if x.get("product_type","vehicle")=="vehicle":st.write(f'里程：**{x["mileage"]:,} km**')
                    if x.get("summary"):st.write(x["summary"])
                    if x["status"]=="active" and x.get("expires_at"):st.caption(f'預計到期：{x["expires_at"]}')
                with st.expander("管理商品",expanded=False):
                    st.markdown(f'#### {x["title"]}　NT$ {x["price"]:,}')
                    st.caption(f'商品 #{x["id"]}｜狀態：{status_label}｜已扣流量：{x["traffic_cost"]}')
                    if imgs:
                        st.caption(f"商品照片：{len(imgs)}/10（第 1 張為商品卡封面）")
                        icols=st.columns(min(5,len(imgs)))
                        for ii,img in enumerate(imgs):
                            with icols[ii%len(icols)]:
                                source=image_source(img)
                                if source is not None:st.image(source,use_container_width=True)
                                st.caption(f"#{ii+1}"+(" 封面" if ii==0 else ""))
                                a,b,c=st.columns(3)
                                if a.button("←",key=f'left_{img["id"]}',disabled=ii==0):
                                    move_image(uid,img["id"],-1);st.rerun()
                                if b.button("→",key=f'right_{img["id"]}',disabled=ii==len(imgs)-1):
                                    move_image(uid,img["id"],1);st.rerun()
                                if c.button("刪",key=f'delimg_{img["id"]}'):
                                    delete_image(uid,img["id"]);st.rerun()
                    uploads=st.file_uploader("新增商品照片（最多 10 張；第 1 張為封面）",type=["jpg","jpeg","png","webp"],accept_multiple_files=True,key=f'photos_{x["id"]}')
                    if uploads and st.button("儲存新增照片",key=f'savephotos_{x["id"]}',use_container_width=True):
                        ok,msg=add_uploaded_images(uid,x["id"],uploads)
                        st.session_state.seller_flash=("success" if ok else "error",msg);st.rerun()
                    if x["status"]=="draft":
                        cost=publication_cost(x["id"])
                        st.info(f'正式上架預計需要 {cost} 流量；目前餘額 {st.session_state.user["traffic_balance"]}。')
                        with st.expander("重新載入／修改草稿"):
                            edit_types=["車輛商品","常規商品"]
                            edit_default="常規商品" if x.get("product_type")=="general" else "車輛商品"
                            edit_type_label=st.selectbox("商品類型",edit_types,index=edit_types.index(edit_default),key=f'edit_type_live_{x["id"]}')
                            edit_product_type="general" if edit_type_label=="常規商品" else "vehicle"
                            if edit_product_type=="general":st.caption("常規商品模式：車輛專屬欄位已隱藏。")
                            with st.form(f'edit_{x["id"]}'):
                                data=_data(f'edit_{x["id"]}_',x,product_type_override=edit_product_type,show_type=False)
                                if st.form_submit_button("儲存修改",use_container_width=True):
                                    ok,msg=update_draft(uid,x["id"],data)
                                    st.session_state.seller_flash=("success" if ok else "error",msg);st.rerun()
                        c1,c2=st.columns(2)
                        if c1.button("正式上架",key=f'pub{x["id"]}',use_container_width=True):
                            ok,msg=publish(uid,x["id"])
                            if ok:
                                st.session_state.seller_flash=("success",msg);st.rerun()
                            else:
                                st.error(msg)
                        if c2.button("前往流量中心",key=f'traffic{x["id"]}',use_container_width=True):
                            st.session_state.page="流量中心";st.rerun()
                        st.divider()
                        st.caption("刪除草稿會永久刪除草稿及其照片，無法復原。")
                        if st.button("🗑 刪除草稿",key=f'delete_draft_{x["id"]}',use_container_width=True):
                            ok,msg=delete_draft(uid,x["id"])
                            st.session_state.seller_flash=("success" if ok else "error",msg);st.rerun()
                    elif x["status"]=="active":
                        st.success("此商品已正式上架並公開顯示。")
                        refund=unlist_refund_preview(uid,x["id"])
                        if x.get("published_at"):st.caption(f'上架時間：{x["published_at"]}')
                        if x.get("expires_at"):st.caption(f'預計到期：{x["expires_at"]}')
                        st.info(f"目前下架預計退還：{refund or 0} 流量（按剩餘上架期間計算；最低流量不退款）")
                        confirm_key=f'confirm_unlist_{x["id"]}'
                        if not st.session_state.get(confirm_key,False):
                            if st.button("下架商品",key=f'unlist_{x["id"]}',use_container_width=True):
                                st.session_state[confirm_key]=True;st.rerun()
                        else:
                            st.warning(f"確定下架？目前預計退還 {refund or 0} 流量。下架後商品會回到草稿並從首頁消失。")
                            u1,u2=st.columns(2)
                            if u1.button("確定下架",key=f'confirm_unlist_btn_{x["id"]}',type="primary",use_container_width=True):
                                ok,msg,amount=unlist(uid,x["id"])
                                if ok:st.session_state.user["traffic_balance"]+=amount
                                st.session_state.pop(confirm_key,None)
                                st.session_state.seller_flash=("success" if ok else "error",msg);st.rerun()
                            if u2.button("取消",key=f'cancel_unlist_{x["id"]}',use_container_width=True):
                                st.session_state.pop(confirm_key,None);st.rerun()
