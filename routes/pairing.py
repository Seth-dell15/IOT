from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

from paho.mqtt import client as mqtt_client
import json
import sqlite3
import main
import asyncio
loop = asyncio.get_event_loop()  # récupère la boucle principale
import database as db
db.init_db()  # initialise la base au lancement
cursor = db.get_cursor()
conn = db.get_conn()
router = APIRouter()

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_SUB = "serrure/rfid"
TOPIC_PUB = "serrure/response"
CLIENT_ID = "serveur_web_securite"
TOPIC_PAIRING_CONFIRM = "serrure/pairing/confirm"

async def notify_clients():
    for ws in main.connections:
        try:
            await ws.send_text("update")
        except:
            main.connections.remove(ws)

@router.post("/pairing/send")
def pairing_send(code: str = Form(...)):
    payload = json.dumps(code)
    mqtt_client_instance.publish("serrure/pairing/request", payload, qos=1, retain=True)
    print(f"Message publié: {payload}")
    return RedirectResponse("/", status_code=303)

# pairing.py
def start_mqtt():
    global mqtt_client_instance
    mqtt_client_instance = connect_mqtt()
    mqtt_client_instance.loop_start()




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
