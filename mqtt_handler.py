import json
from paho.mqtt import client as mqtt_client
from db import cursor, conn
from utils import loop, notify_clients

BROKER = "broker.emqx.io"
PORT = 1883
CLIENT_ID = "serveur_web_securite"
TOPIC_SUB = "serrure/rfid"
TOPIC_PUB = "serrure/response"
TOPIC_PAIRING_CONFIRM = "serrure/pairing/confirm"

client = None

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT ✅")
        client.subscribe(TOPIC_SUB)
        client.subscribe(TOPIC_PAIRING_CONFIRM)
    else:
        print(f"Erreur de connexion MQTT, code={rc}")

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
            cursor.execute(
                "INSERT OR IGNORE INTO serrures (uid, nom, roles_autorises) VALUES (?, ?, ?)",
                (uid_serrure, uid_serrure, "")
            )
            conn.commit()
            print(f"Serrure appairée ✅ UID={uid_serrure}")
            loop.call_soon_threadsafe(lambda: loop.create_task(notify_clients()))
        return

    # ---------- Lecture normale d'une carte ----------
    uid_carte = data.get("uid_carte", "").upper()
    uid_serrure = data.get("uid_serrure", "Accueil")
    
    if not uid_carte:
        print("UID carte manquant dans le JSON")
        return

    # Vérifier la carte
    cursor.execute("SELECT role FROM cartes WHERE uid = ?", (uid_carte,))
    result = cursor.fetchone()
    role = result[0] if result else "invité"

    if not result:
        print(f"Carte inconnue détectée : {uid_carte} -> ajout comme invité")
        try:
            cursor.execute("INSERT INTO cartes (uid, role) VALUES (?, ?)", (uid_carte, role))
            conn.commit()
        except:
            pass

    # Vérifier la serrure
    cursor.execute("SELECT nom, roles_autorises FROM serrures WHERE uid = ?", (uid_serrure,))
    serrure_result = cursor.fetchone()

    if serrure_result:
        nom_serrure, roles_autorises = serrure_result[0], [r.strip() for r in serrure_result[1].split(",")]
        action = "OPEN" if role in roles_autorises else "DENY"
        print(f"Accès {'autorisé' if action=='OPEN' else 'refusé'} {'✅' if action=='OPEN' else '❌'} Carte={uid_carte} Rôle={role} Serrure={nom_serrure}")
        client.publish(TOPIC_PUB, "Acces autorise" if action=="OPEN" else "Acces refuse")
    else:
        nom_serrure = uid_serrure
        roles_autorises = ""
        cursor.execute("INSERT OR IGNORE INTO serrures (uid, nom, roles_autorises) VALUES (?, ?, ?)",
                       (uid_serrure, nom_serrure, roles_autorises))
        conn.commit()
        action = "DENY"
        print(f"Serrure inconnue détectée ❌ UID={uid_serrure} -> ajout automatique")
        client.publish(TOPIC_PUB, "Serrure inconnue")

    # Log
    cursor.execute("INSERT INTO logs (uid_carte, uid_serrure, role, action) VALUES (?, ?, ?, ?)",
                   (uid_carte, nom_serrure, role, action))
    conn.commit()

    # Notifier le front
    loop.call_soon_threadsafe(lambda: loop.create_task(notify_clients()))

def connect_mqtt():
    global client
    client = mqtt_client.Client(CLIENT_ID)
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(BROKER, PORT)
    client.loop_start()
    return client
