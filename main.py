# main.py

## Lancer le serveur : python -m uvicorn main:app --reload

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from paho.mqtt import client as mqtt_client
import sqlite3

app = FastAPI(title="Serrure connectée")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_SUB = "serrure/rfid"
TOPIC_PUB = "serrure/response"
CLIENT_ID = "serveur_web_securite"

# --- Base de donnée SQLite ---
conn = sqlite3.connect("serrure.db", check_same_thread=False)
cursor = conn.cursor()

# Table cartes
cursor.execute("""
CREATE TABLE IF NOT EXISTS cartes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT UNIQUE,
    role TEXT
)
""")

# Table serrures
cursor.execute("""
CREATE TABLE IF NOT EXISTS serrures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT UNIQUE,
    nom TEXT,
    roles_autorises TEXT
)
""")

# Table roles
cursor.execute("""
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT UNIQUE
)
""")

# Table logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid_carte TEXT,
    uid_serrure TEXT,
    role TEXT,
    action TEXT,
    date_utilisation DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")


conn.commit()

# ------------------------------------------------------------------------
#                 ROUTES : AJOUT / SUPPRESSION
# ------------------------------------------------------------------------

@app.post("/serrures/ajouter")
def ajouter_serrure(uid: str = Form(...), nom: str = Form(...), roles_autorises: str = Form(...)):
    try:
        cursor.execute("INSERT INTO serrures (uid, nom, roles_autorises) VALUES (?, ?, ?)",
                       (uid, nom, roles_autorises))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    return RedirectResponse("/", status_code=303)


@app.post("/serrures/supprimer")
def supprimer_serrure(uid: str = Form(...)):
    cursor.execute("DELETE FROM serrures WHERE uid = ?", (uid,))
    conn.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/roles/ajouter")
def ajouter_role(nom: str = Form(...)):
    try:
        cursor.execute("INSERT INTO roles (nom) VALUES (?)", (nom,))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    return RedirectResponse("/", status_code=303)


@app.post("/roles/supprimer")
def supprimer_role(nom: str = Form(...)):
    cursor.execute("DELETE FROM roles WHERE nom = ?", (nom,))
    conn.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/cartes", response_class=HTMLResponse)
def cartes_page(request: Request):
    cursor.execute("SELECT id, uid, role FROM cartes")
    cartes = cursor.fetchall()
    return templates.TemplateResponse("cartes.html", {"request": request, "cartes": cartes})


@app.post("/cartes/ajouter")
def cartes_ajouter(request: Request, uid: str = Form(...), role: str = Form(...)):
    cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", (uid, role))
    conn.commit()
    return RedirectResponse("/cartes", status_code=303)


@app.post("/cartes/supprimer/{id}")
def cartes_supprimer(id: int):
    cursor.execute("DELETE FROM cartes WHERE id = ?", (id,))
    conn.commit()
    return RedirectResponse("/cartes", status_code=303)


# ------------------------------------------------------------------------
#                 ROUTE PRINCIPALE : PAGE WEB
# ------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
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


# ------------------------------------------------------------------------
#                 MQTT : RÉCEPTION CARTE + RÉPONSE
# ------------------------------------------------------------------------

def on_message(client, userdata, msg):
    # Récupérer l'UID depuis MQTT et le nettoyer
    uid = msg.payload.decode().strip().upper()
    print(f"[MQTT] Carte détectée : '{uid}'")

    # Vérifier si l'UID appartient à une carte existante
    cursor.execute("SELECT role FROM cartes WHERE uid = ?", (uid,))
    result = cursor.fetchone()

    if result:
        role = result[0]
        action = "OPEN"
        print(f"Carte autorisée ✅ (UID={uid}, rôle={role})")
        client.publish(TOPIC_PUB, "Accès autorisé")
    else:
        role = "inconnu"
        action = "DENY"
        print(f"Carte refusée ❌ (UID={uid})")
        client.publish(TOPIC_PUB, "Accès refusé")

    # Par défaut : nom de la serrure
    uid_serrure = "Accueil"

    # Enregistrer dans les logs (date automatique)
    cursor.execute(
        "INSERT INTO logs (uid_carte, uid_serrure, role, action) VALUES (?, ?, ?, ?)",
        (uid, uid_serrure, role, action)
    )
    conn.commit()


    # -------------------------------------



def connect_mqtt():
    client = mqtt_client.Client(CLIENT_ID)
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.subscribe(TOPIC_SUB)
    return client


@app.on_event("startup")
async def startup_event():
    global mqtt_client_instance
    mqtt_client_instance = connect_mqtt()
    mqtt_client_instance.loop_start()
    print("Serveur et MQTT connectés ✅")

    # Carte de test
    try:
        cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", ("123456ABCD", "admin"))
        conn.commit()
        print("UID de test ajouté à la base")
    except sqlite3.IntegrityError:
        pass
