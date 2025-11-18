from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from db import cursor, conn
from typing import List

router = APIRouter()

@router.post("/serrures/ajouter")
def ajouter_serrure(uid: str = Form(...), nom: str = Form(...), roles_autorises: List[str] = Form(default=[])):
    roles_str = ",".join(roles_autorises)
    try:
        cursor.execute("INSERT INTO serrures (uid, nom, roles_autorises) VALUES (?, ?, ?)",
                       (uid, nom, roles_str))
        conn.commit()
    except:
        pass
    return RedirectResponse("/", status_code=303)

@router.post("/serrures/supprimer")
def supprimer_serrure(uid: str = Form(...)):
    cursor.execute("DELETE FROM serrures WHERE uid = ?", (uid,))
    conn.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/serrures/modifier_nom/{uid}")
def modifier_nom_serrure(uid: str, nom: str = Form(...)):
    cursor.execute("UPDATE serrures SET nom = ? WHERE uid = ?", (nom, uid))
    conn.commit()
    return RedirectResponse("/", status_code=303)

@router.post("/serrures/modifier_roles/{uid}")
def modifier_roles(uid: str, roles_autorises: List[str] = Form(...)):
    roles_str = ",".join(roles_autorises)
    cursor.execute("UPDATE serrures SET roles_autorises = ? WHERE uid = ?", (roles_str, uid))
    conn.commit()
    return RedirectResponse("/", status_code=303)
