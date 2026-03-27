import asyncio
import json
import logging
import random
import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from models.detector import Simulator
from routes.api import router as api_router

logging.basicConfig(level=logging.INFO)

START_TIME = time.time()

# ── Shared state ─────────────────────────────────────────────
sim = Simulator()
active_connections: list[WebSocket] = []


async def broadcast(msg: dict):
    data = json.dumps(msg)
    for connection in list(active_connections):
        try:
            await connection.send_text(data)
        except Exception:
            if connection in active_connections:
                active_connections.remove(connection)

# ── Simulation loop ──────────────────────────────────────────


async def simulation_loop():
    while True:
        try:
            tx = sim.generate()
            await broadcast({"type": "TRANSACTION", "data": tx})

            if tx.get("status") == "fraud":
                await broadcast({"type": "FRAUD_ALERT", "data": tx})

            stats = sim.getStats()
            if stats.get("total", 0) % 6 == 0:
                await broadcast({"type": "STATS", "data": stats})

            if stats.get("total", 0) % 30 == 0:
                sim.flTick()
                await broadcast({
                    "type": "FL_UPDATE",
                    "data": {
                        "round": sim.flRound,
                        "accuracy": sim.accuracy,
                        "epsilon": sim.epsilon
                    }
                })
        except Exception as e:
            logging.error(f"Error in simulation loop: {e}")

        delay = 0.400 + random.random() * 0.900
        await asyncio.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.sim = sim
    app.state.broadcast = broadcast
    app.state.start_time = START_TIME

    # Start simulation loop in background
    task = asyncio.create_task(simulation_loop())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

# ── Middleware ───────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── API routes ───────────────────────────────────────────────
app.include_router(api_router, prefix="/api")

# ── WebSocket ────────────────────────────────────────────────


@app.websocket("/")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)

    try:
        await websocket.send_text(json.dumps({
            "type": "CONNECTED",
            "stats": sim.getStats()
        }))

        while True:
            raw = await websocket.receive_text()
            try:
                m = json.loads(raw)
                if m.get("type") == "PING":
                    await websocket.send_text(json.dumps({"type": "PONG"}))
                elif m.get("type") == "TRIGGER":
                    fraud_type = m.get("fraudType")
                    tx = sim.generate(fraud_type)
                    await broadcast({"type": "TRANSACTION", "data": tx})
                    await broadcast({"type": "FRAUD_ALERT", "data": tx})
                    await broadcast({"type": "STATS", "data": sim.getStats()})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        if websocket in active_connections:
            active_connections.remove(websocket)
    except Exception as e:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logging.error(f"WebSocket Error: {e}")

# ── Static files ─────────────────────────────────────────────
# Mount static files at the end to avoid intercepting API/WS routes
public_path = os.path.join(os.path.dirname(__file__), "public")
if os.path.isdir(public_path):
    app.mount("/", StaticFiles(directory=public_path, html=True), name="public")

if __name__ == "__main__":
    import uvicorn
    print(
        "\n\x1b[36m╔══════════════════════════════════════════════════════════╗\x1b[0m")
    print("\x1b[36m║\x1b[0m  \x1b[1m\x1b[32m PFLF — Privacy-Preserving Federated Learning\x1b[0m              \x1b[36m║\x1b[0m")
    print("\x1b[36m║\x1b[0m  \x1b[33m Financial Fraud Detection System v2.0 (Python)\x1b[0m            \x1b[36m║\x1b[0m")
    print(
        "\x1b[36m╠══════════════════════════════════════════════════════════╣\x1b[0m")
    print("\x1b[36m║\x1b[0m  🌐 Open browser: \x1b[4m\x1b[35mhttp://localhost:3000\x1b[0m                      \x1b[36m║\x1b[0m")
    print("\x1b[36m║\x1b[0m  📡 API base:     \x1b[4m\x1b[35mhttp://localhost:3000/api\x1b[0m                  \x1b[36m║\x1b[0m")
    print(
        "\x1b[36m╚══════════════════════════════════════════════════════════╝\x1b[0m")
    uvicorn.run("main:app", host="0.0.0.0", port=3000,
                reload=True, ws_max_size=1048576)
