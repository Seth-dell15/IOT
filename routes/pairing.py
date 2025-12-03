from fastapi import FastAPI
from routes import cartes, serrures, roles, logs, pairing

app = FastAPI(title="Serrure connectée")

# Routers
app.include_router(cartes.router)
app.include_router(serrures.router)
app.include_router(roles.router)
app.include_router(logs.router)
app.include_router(pairing.router)

# WebSocket + MQTT startup
connections = []
from routes.pairing import start_mqtt

@app.on_event("startup")
async def startup_event():
    start_mqtt()
