from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from db import cursor, conn

router = APIRouter()

@router.post("/logs/vider")
def vider_logs():
    cursor.execute("DELETE FROM logs")
    conn.commit()
    return RedirectResponse("/", status_code=303)
