# # main.py

# ## Lancer le serveur : python -m uvicorn main:app --reload

# ## Exemple de réponse attendu 
# # {
# #     "uid_carte": "123456ABCD",
# #     "uid_serrure": "01"
# # }


from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from db import init_db
from routes import cartes, serrures, roles, logs
from mqtt_handler import connect_mqtt

from utils import connections, notify_clients
from routes.index import router as index_router

app = FastAPI(title="Serrure connectée")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialisation DB
init_db()

# Inclure les routes
app.include_router(index_router)
app.include_router(cartes.router)
app.include_router(serrures.router)
app.include_router(roles.router)
app.include_router(logs.router)

# WebSocket
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connections.remove(websocket)

# Lancement MQTT
@app.on_event("startup")
async def startup_event():
    global mqtt_client_instance
    mqtt_client_instance = connect_mqtt()
    mqtt_client_instance.loop_start()
