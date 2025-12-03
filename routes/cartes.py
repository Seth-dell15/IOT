from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
import sqlite3
from fastapi.templating import Jinja2Templates
from database import get_cursor, get_conn

templates = Jinja2Templates(directory="templates")
cursor = get_cursor()
conn = get_conn()

router = APIRouter()

@router.get("/cartes", response_class=HTMLResponse)
def cartes_page(request: Request):
    cursor.execute("SELECT id, uid, role FROM cartes")
    cartes = cursor.fetchall()
    return templates.TemplateResponse("cartes.html", {"request": request, "cartes": cartes})


@router.post("/cartes/ajouter")
def cartes_ajouter(uid: str = Form(...), roles_autorises: list[str] = Form(default=["invité"])):
    roles_str = ",".join(roles_autorises)
    try:
        cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", (uid, roles_str))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    return RedirectResponse("/", status_code=303)




@router.post("/cartes/modifier_roles/{uid}")
def cartes_modifier_roles(uid: str, roles_autorises: list[str] = Form(...)):
    roles_str = ",".join(roles_autorises)
    cursor.execute("UPDATE cartes SET role = ? WHERE uid = ?", (roles_str, uid))
    conn.commit()
    return RedirectResponse("/", status_code=303)



@router.post("/cartes/supprimer")
def cartes_supprimer(uid: str = Form(...)):
    cursor.execute("DELETE FROM cartes WHERE uid = ?", (uid,))
    conn.commit()
    return RedirectResponse("/", status_code=303)  # <-- redirection vers la page principale
