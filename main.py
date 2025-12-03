# main.py

## Lancer le serveur : python -m uvicorn main:app --reload

## Exemple de réponse attendu 
# {
#     "uid_carte": "123456ABCD",
#     "uid_serrure": "01"
# }

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from paho.mqtt import client as mqtt_client
import sqlite3
import json
from typing import List

app = FastAPI(title="Serrure connectée")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_SUB = "serrure/rfid"
TOPIC_PUB = "serrure/response"
CLIENT_ID = "serveur_web_securite"
TOPIC_PAIRING_CONFIRM = "serrure/pairing/confirm"


# --- Base de donnée SQLite ---
import database as db
db.init_db()  # initialise la base au lancement
cursor = db.get_cursor()
conn = db.get_conn()


from fastapi import WebSocket
import asyncio
loop = asyncio.get_event_loop()  # récupère la boucle principale


connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connections.remove(websocket)

async def notify_clients():
    for ws in connections:
        try:
            await ws.send_text("update")
        except:
            connections.remove(ws)

# ------------------------------------------------------------------------
#                 ROUTES : AJOUT / SUPPRESSION
# ------------------------------------------------------------------------


@app.post("/pairing/send")
def pairing_send(code: str = Form(...)):
    payload = json.dumps(code)
    mqtt_client_instance.publish("serrure/pairing/request", payload, qos=1, retain=True)
    print(f"Message publié: {payload}")
    return RedirectResponse("/", status_code=303)




@app.post("/serrures/ajouter")
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



@app.post("/serrures/supprimer")
def supprimer_serrure(uid: str = Form(...)):
    cursor.execute("DELETE FROM serrures WHERE uid = ?", (uid,))
    conn.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/serrures/modifier_nom/{uid}")
def modifier_nom_serrure(uid: str, nom: str = Form(...)):
    cursor.execute("UPDATE serrures SET nom = ? WHERE uid = ?", (nom, uid))
    conn.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/serrures/modifier_roles/{uid}")
async def modifier_roles(uid: str, roles_autorises: list[str] = Form(...)):
    roles = ",".join(roles_autorises)
    cursor.execute("UPDATE serrures SET roles_autorises = ? WHERE uid = ?", (roles, uid))
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
def cartes_ajouter(uid: str = Form(...), roles_autorises: list[str] = Form(default=["invité"])):
    roles_str = ",".join(roles_autorises)
    try:
        cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", (uid, roles_str))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    return RedirectResponse("/", status_code=303)




@app.post("/cartes/modifier_roles/{uid}")
def cartes_modifier_roles(uid: str, roles_autorises: list[str] = Form(...)):
    roles_str = ",".join(roles_autorises)
    cursor.execute("UPDATE cartes SET role = ? WHERE uid = ?", (roles_str, uid))
    conn.commit()
    return RedirectResponse("/", status_code=303)



@app.post("/cartes/supprimer")
def cartes_supprimer(uid: str = Form(...)):
    cursor.execute("DELETE FROM cartes WHERE uid = ?", (uid,))
    conn.commit()
    return RedirectResponse("/", status_code=303)  # <-- redirection vers la page principale





@app.post("/logs/vider")
def vider_logs():
    cursor.execute("DELETE FROM logs")
    conn.commit()
    return RedirectResponse("/", status_code=303)

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
    try:
        data = json.loads(msg.payload.decode().strip())
    except json.JSONDecodeError:
        print("Message MQTT invalide, doit être un JSON")
        return

    topic = msg.topic

    # ---------- Gérer le pairing ----------
    if topic == TOPIC_PAIRING_CONFIRM:
        uid_serrure = data.get("uid_serrure")
        status = data.get("status")
        if status == "ok" and uid_serrure:
            # Ajouter la serrure si elle n'existe pas déjà
            cursor.execute(
                "INSERT OR IGNORE INTO serrures (uid, nom, roles_autorises) VALUES (?, ?, ?)",
                (uid_serrure, uid_serrure, "")  # nom = uid par défaut, roles vide
            )
            conn.commit()
            print(f"Serrure appairée ✅ UID={uid_serrure}")

            # Notifier le front
            loop.call_soon_threadsafe(asyncio.create_task, notify_clients())
        return  # on ne continue pas la partie carte/serrure normale

    # ---------- Gérer la lecture normale d'une carte ----------
    uid_carte = data.get("uid_carte", "").upper()
    uid_serrure = data.get("uid_serrure", "Accueil")
    
    if not uid_carte:
        print("UID carte manquant dans le JSON")
        return

    # Vérifier la carte
    cursor.execute("SELECT role FROM cartes WHERE uid = ?", (uid_carte,))
    result = cursor.fetchone()

    if result:
        role = result[0]
    else:
        role = "invité"
        print(f"Carte inconnue détectée : {uid_carte} -> ajout comme invité")
        try:
            cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", (uid_carte, role))
            conn.commit()
        except sqlite3.IntegrityError:
            pass

    # Vérifier la serrure
    cursor.execute("SELECT nom, roles_autorises FROM serrures WHERE uid = ?", (uid_serrure,))
    serrure_result = cursor.fetchone()

    if serrure_result:
        nom_serrure, roles_autorises = serrure_result[0], [r.strip() for r in serrure_result[1].split(",")]
        if role in roles_autorises:
            action = "OPEN"
            print(f"Accès autorisé ✅ Carte={uid_carte} Rôle={role} Serrure={nom_serrure}")
            client.publish(TOPIC_PUB, "Acces autorise")
        else:
            action = "DENY"
            print(f"Accès refusé ❌ Carte={uid_carte} Rôle={role} Serrure={nom_serrure}")
            client.publish(TOPIC_PUB, "Acces refuse")
    else:
        # Ajouter la serrure inconnue avec rôle vide ou par défaut
        nom_serrure = uid_serrure  # On met l'UID comme nom par défaut
        roles_autorises = ""       # Aucun rôle autorisé par défaut
        cursor.execute(
            "INSERT OR IGNORE INTO serrures (uid, nom, roles_autorises) VALUES (?, ?, ?)",
            (uid_serrure, nom_serrure, roles_autorises)
        )
        conn.commit()

        action = "DENY"
        print(f"Serrure inconnue détectée ❌ UID={uid_serrure} -> ajout automatique")
        client.publish(TOPIC_PUB, "Serrure inconnue")



    # Enregistrer le log
    cursor.execute(
    "INSERT INTO logs (uid_carte, uid_serrure, role, action) VALUES (?, ?, ?, ?)",
    (uid_carte, nom_serrure, role, action)  # <-- ici on met le nom
    )
    conn.commit()


    # Notifier le front
    loop.call_soon_threadsafe(asyncio.create_task, notify_clients())


    # -------------------------------------


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT ✅")
        # S'abonner aux topics
        client.subscribe(TOPIC_SUB)
        client.subscribe(TOPIC_PAIRING_CONFIRM)
    else:
        print(f"Erreur de connexion MQTT, code={rc}")

def connect_mqtt():
    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_start()
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
