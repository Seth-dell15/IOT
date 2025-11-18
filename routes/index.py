# routes/index.py
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
def index(request: Request):
    conn = sqlite3.connect("serrure.db")
    cursor = conn.cursor()

    cursor.execute("SELECT uid, role FROM cartes")
    cartes = cursor.fetchall()

    cursor.execute("SELECT * FROM serrures")
    serrures = cursor.fetchall()

    cursor.execute("SELECT * FROM logs ORDER BY date_utilisation DESC LIMIT 50")
    logs = cursor.fetchall()

    cursor.execute("SELECT * FROM roles")
    roles = cursor.fetchall()

    conn.close()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "cartes": cartes,
        "serrures": serrures,
        "logs": logs,
        "roles": roles
    })
