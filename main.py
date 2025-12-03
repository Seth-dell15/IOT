from fastapi import FastAPI, WebSocket
from routes import cartes, serrures, roles, logs, pairing, index
app = FastAPI(title="Serrure connectée")

# Routers
app.include_router(index.router)
app.include_router(cartes.router)
app.include_router(serrures.router)
app.include_router(roles.router)
app.include_router(logs.router)
app.include_router(pairing.router)

# WebSocket + MQTT startup
connections = []
from routes.pairing import start_mqtt

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connections.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        connections.remove(websocket)

@app.on_event("startup")
async def startup_event():
    start_mqtt()

