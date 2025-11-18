from fastapi import APIRouter, Form, Request
from fastapi.responses import RedirectResponse
from db import cursor, conn
from typing import List

router = APIRouter()

@router.post("/cartes/ajouter")
def cartes_ajouter(uid: str = Form(...), roles_autorises: List[str] = Form(default=["invité"])):
    roles_str = ",".join(roles_autorises)
    try:
        cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", (uid, roles_str))
        conn.commit()
    except:
        pass
    return RedirectResponse("/", status_code=303)

@router.post("/cartes/supprimer")
def cartes_supprimer(uid: str = Form(...)):
    cursor.execute("DELETE FROM cartes WHERE uid = ?", (uid,))
    conn.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/cartes/modifier_roles/{uid}")
def cartes_modifier_roles(uid: str, roles_autorises: List[str] = Form(...)):
    roles_str = ",".join(roles_autorises)
    cursor.execute("UPDATE cartes SET role = ? WHERE uid = ?", (roles_str, uid))
    conn.commit()
    return RedirectResponse("/", status_code=303)
