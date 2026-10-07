import io
import json
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from backend.database import PROJECT_ROOT,DATABASE_URL
from backend.services.admin_service import settings

def make_backup():
    stamp=datetime.now().strftime("%Y%m%d_%H%M%S")
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",zipfile.ZIP_DEFLATED) as z:
        if DATABASE_URL.startswith("sqlite"):
            db_path=PROJECT_ROOT/"data"/"vehicle_market.db"
            if db_path.exists():
                snapshot=PROJECT_ROOT/"data"/"_backup_snapshot.db"
                src=sqlite3.connect(str(db_path))
                dst=sqlite3.connect(str(snapshot))
                src.backup(dst)
                dst.close()
                src.close()
                z.write(snapshot,"database/vehicle_market.db")
                snapshot.unlink(missing_ok=True)
        else:
            z.writestr("database/README.txt","External database is configured. Use the database provider's backup/export mechanism for a full database dump.")
        upload_dir=PROJECT_ROOT/"storage"/"uploads"
        if upload_dir.exists():
            for p in upload_dir.rglob("*"):
                if p.is_file() and p.name!=".gitkeep":
                    z.write(p,f"uploads/{p.relative_to(upload_dir)}")
        z.writestr("system/settings.json",json.dumps(settings(),ensure_ascii=False,indent=2))
        z.writestr("system/backup_info.json",json.dumps({
            "created_at":datetime.now().isoformat(),
            "format_version":2,
            "database_url_type":"sqlite" if DATABASE_URL.startswith("sqlite") else "external"
        },ensure_ascii=False,indent=2))
    mem.seek(0)
    return f"vehicle_market_backup_{stamp}.zip",mem.getvalue()
