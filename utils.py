import asyncio

connections = []
loop = asyncio.get_event_loop()

async def notify_clients():
    for ws in connections:
        try:
            await ws.send_text("update")
        except:
            connections.remove(ws)
