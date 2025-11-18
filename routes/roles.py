from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
from db import cursor, conn

router = APIRouter()

@router.post("/roles/ajouter")
def ajouter_role(nom: str = Form(...)):
    try:
        cursor.execute("INSERT INTO roles (nom) VALUES (?)", (nom,))
        conn.commit()
    except:
        pass
    return RedirectResponse("/", status_code=303)

@router.post("/roles/supprimer")
def supprimer_role(nom: str = Form(...)):
    cursor.execute("DELETE FROM roles WHERE nom = ?", (nom,))
    conn.commit()
    return RedirectResponse("/", status_code=303)
