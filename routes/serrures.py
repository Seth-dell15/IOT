from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
import sqlite3
from database import get_cursor, get_conn
from typing import List

cursor = get_cursor()
conn = get_conn()

router = APIRouter()

@router.post("/serrures/ajouter")
def ajouter_serrure(
    uid: str = Form(...),
    nom: str = Form(...),
    roles_autorises: List[str] = Form(default=[])  # ← liste vide si rien n'est sélectionné
):
    roles_str = ",".join(roles_autorises)  # transforme la liste en chaîne
    try:
        cursor.execute(
            "INSERT INTO serrures (uid, nom, roles_autorises) VALUES (?, ?, ?)",
            (uid, nom, roles_str)
        )
        conn.commit()
    except sqlite3.IntegrityError:
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
async def modifier_roles(uid: str, roles_autorises: list[str] = Form(...)):
    roles = ",".join(roles_autorises)
    cursor.execute("UPDATE serrures SET roles_autorises = ? WHERE uid = ?", (roles, uid))
    conn.commit()
    return RedirectResponse("/", status_code=303)
