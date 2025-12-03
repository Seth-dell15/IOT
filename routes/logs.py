from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from database import get_cursor, get_conn

cursor = get_cursor()
conn = get_conn()

router = APIRouter()

@router.post("/logs/vider")
def vider_logs():
    cursor.execute("DELETE FROM logs")
    conn.commit()
    return RedirectResponse("/", status_code=303)
