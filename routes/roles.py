from fastapi import APIRouter, Form
from fastapi.responses import RedirectResponse
import sqlite3
from database import get_cursor, get_conn

cursor = get_cursor()
conn = get_conn()

router = APIRouter()

@router.post("/roles/ajouter")
def ajouter_role(nom: str = Form(...)):
    try:
        cursor.execute("INSERT INTO roles (nom) VALUES (?)", (nom,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    return RedirectResponse("/", status_code=303)


@router.post("/roles/supprimer")
def supprimer_role(nom: str = Form(...)):
    cursor.execute("DELETE FROM roles WHERE nom = ?", (nom,))
    conn.commit()
    return RedirectResponse("/", status_code=303)
