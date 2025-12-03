from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
import sqlite3
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")
router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    conn_local = sqlite3.connect("serrure.db")
    cursor_local = conn_local.cursor()

    cursor_local.execute("SELECT uid, role FROM cartes")
    cartes = cursor_local.fetchall()

    cursor_local.execute("SELECT * FROM serrures")
    serrures = cursor_local.fetchall()

    cursor_local.execute("SELECT * FROM logs ORDER BY date_utilisation DESC LIMIT 50")
    logs = cursor_local.fetchall()

    cursor_local.execute("SELECT * FROM roles")
    roles = cursor_local.fetchall()

    conn_local.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "cartes": cartes,
        "serrures": serrures,
        "logs": logs,
        "roles": roles
    })