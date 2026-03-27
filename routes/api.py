from fastapi import APIRouter, Request, HTTPException
import time
from datetime import datetime
from models.detector import analyzeCC, analyzeML, analyzeUT, analyzeFT, analyzeIT

router = APIRouter()


@router.get("/health")
async def get_health(request: Request):
    uptime_seconds = int(time.time() - request.app.state.start_time)
    return {
        "success": True,
        "status": "operational",
        "version": "2.0.0",
        "uptime": f"{uptime_seconds}s",
        "timestamp": datetime.utcnow().isoformat() + 'Z',
        "services": {
            "simulator": "running",
            "websocket": "active",
            "federated_learning": "training",
            "differential_privacy": "enabled"
        }
    }


@router.get("/stats")
async def get_stats(request: Request):
    sim = request.app.state.sim
    return {"success": True, "data": sim.getStats()}


@router.get("/transactions")
async def get_transactions(request: Request, limit: int = 100):
    sim = request.app.state.sim
    limit = min(limit, 500)
    data = sim.transactions[:limit]
    return {
        "success": True,
        "count": len(data),
        "data": data
    }


@router.get("/banks")
async def get_banks(request: Request):
    sim = request.app.state.sim
    return {"success": True, "data": sim.getBanks()}


@router.post("/analyze/cc")
async def post_analyze_cc(payload: dict):
    try:
        result = analyzeCC(payload)
        return {"success": True, "type": "CC", "endpoint": "/api/analyze/cc", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/ml")
async def post_analyze_ml(payload: dict):
    try:
        result = analyzeML(payload)
        return {"success": True, "type": "ML", "endpoint": "/api/analyze/ml", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/ut")
async def post_analyze_ut(payload: dict):
    try:
        result = analyzeUT(payload)
        return {"success": True, "type": "UT", "endpoint": "/api/analyze/ut", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/ft")
async def post_analyze_ft(payload: dict):
    try:
        result = analyzeFT(payload)
        return {"success": True, "type": "FT", "endpoint": "/api/analyze/ft", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/analyze/it")
async def post_analyze_it(payload: dict):
    try:
        result = analyzeIT(payload)
        return {"success": True, "type": "IT", "endpoint": "/api/analyze/it", "data": result}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/trigger/{type_name}")
async def trigger_event(request: Request, type_name: str):
    type_name = type_name.upper()
    valid_types = ['CC', 'ML', 'UT', 'FT', 'IT']

    if type_name not in valid_types:
        raise HTTPException(
            status_code=400, detail=f"Invalid type. Use: {'|'.join(valid_types)}")

    sim = request.app.state.sim
    broadcast = request.app.state.broadcast

    tx = sim.generate(type_name)

    await broadcast({"type": "TRANSACTION", "data": tx})
    await broadcast({"type": "FRAUD_ALERT", "data": tx})
    await broadcast({"type": "STATS", "data": sim.getStats()})

    return {
        "success": True,
        "message": f"{type_name} fraud event triggered",
        "data": tx
    }
