import json
import urllib.request
from backend.cloud_config import secret

def send_verification_email(to_email,code):
    api_key=secret("RESEND_API_KEY")
    sender=secret("EMAIL_FROM")
    if not api_key or not sender:
        return False,"Email 寄送服務尚未設定"
    payload=json.dumps({
        "from":sender,
        "to":[to_email],
        "subject":"RuiderCar Email 驗證碼",
        "html":f"<h2>RuiderCar Email 驗證</h2><p>您的驗證碼為：</p><h1>{code}</h1><p>驗證碼 10 分鐘內有效。若不是您本人操作，請忽略此信。</p>"
    }).encode("utf-8")
    req=urllib.request.Request("https://api.resend.com/emails",data=payload,method="POST",headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json","User-Agent":"RuiderCar/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=15) as response:
            return 200<=response.status<300,"驗證信已寄出"
    except Exception:
        return False,"驗證信寄送失敗，請稍後再試"
