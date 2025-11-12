# main.py

## Code pour lancer le serveur : python -m uvicorn main:app --reload
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from paho.mqtt import client as mqtt_client
import sqlite3
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Serrure connectée")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_SUB = "serrure/rfid"
TOPIC_PUB = "serrure/response"
CLIENT_ID = "serveur_web_securite"

# --- Base SQLite ---
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

# Ajouter colonne role_id seulement si elle n'existe pas (attention aux erreurs si déjà ajoutée)
try:
    cursor.execute("ALTER TABLE cartes ADD COLUMN role_id INTEGER REFERENCES roles(id)")
except sqlite3.OperationalError:
    # colonne déjà existante
    pass

# Table logs
cursor.execute("""
CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid_carte TEXT,
    uid_serrure TEXT,
    date_utilisation DATETIME DEFAULT CURRENT_TIMESTAMP
)
""")

conn.commit()



# --- Route web ---
@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    conn_local = sqlite3.connect("serrure.db")
    cursor_local = conn_local.cursor()

    # Cartes
    cursor_local.execute("SELECT uid, role FROM cartes")
    cartes = cursor_local.fetchall()

    # Serrures
    cursor_local.execute("SELECT * FROM serrures")
    serrures = cursor_local.fetchall()

    # Logs
    cursor_local.execute("SELECT * FROM logs ORDER BY date_utilisation DESC LIMIT 50")
    logs = cursor_local.fetchall()

    conn_local.close()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "cartes": cartes,
        "serrures": serrures,
        "logs": logs
    })


# --- MQTT ---
def on_message(client, userdata, msg):
    uid = msg.payload.decode().strip()
    print(f"[MQTT] Carte détectée : '{uid}'")

    # Afficher les UID actuels dans la base
    cursor.execute("SELECT uid, role FROM cartes")
    cartes = cursor.fetchall()
    print(f"[SQLite] Cartes actuellement dans la base : {cartes}")

    # Vérifier si l'UID est dans la base
    cursor.execute("SELECT role FROM cartes WHERE uid = ?", (uid,))
    result = cursor.fetchone()

    if result:
        print(f"Carte autorisée ✅ (rôle: {result[0]})")
        client.publish(TOPIC_PUB, "open")
    else:
        print("Carte non reconnue ❌")
        client.publish(TOPIC_PUB, "deny")




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

    # --- Ajouter un UID pour test ---
    try:
        cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", ("123456ABCD", "admin"))
        conn.commit()
        print("UID de test ajouté à la base ✅")
    except sqlite3.IntegrityError:
        # UID déjà présent
        pass

