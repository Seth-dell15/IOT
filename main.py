# main.py

## Code pour lancer le serveur : python -m uvicorn main:app --reload
from fastapi import FastAPI
from paho.mqtt import client as mqtt_client
import sqlite3

app = FastAPI(title="Serrure connectée")

BROKER = "broker.emqx.io"
PORT = 1883
TOPIC_SUB = "serrure/rfid"
TOPIC_PUB = "serrure/response"
CLIENT_ID = "serveur_web_securite"

# --- Base SQLite ---
conn = sqlite3.connect("serrure.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS cartes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT UNIQUE,
    role TEXT
)
""")
conn.commit()

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

@app.get("/")
def root():
    return {"status": "Serveur serrure en ligne"}
