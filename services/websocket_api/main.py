from fastapi import FastAPI, HTTPException, Query
from utils.schemas import OHLCVRequest, StreamUpdateRequest, StreamResponse, StreamListResponse
from services.websocket_api.websocket_data import start_stream, stop_stream, update_stream, STREAMS

app = FastAPI()

@app.post("/start", response_model=StreamResponse)
async def start_streaming(req: OHLCVRequest):
    key = (req.symbol.lower(), req.interval)
    if key in STREAMS:
        raise HTTPException(status_code=400, detail=f"Stream already running for {req.symbol}@{req.interval}")
    await start_stream(key)
    return StreamResponse(message=f"✅ Started streaming for {req.symbol}@{req.interval}")

@app.post("/stop", response_model=StreamResponse)
async def stop_streaming(req: OHLCVRequest):
    key = (req.symbol.lower(), req.interval)
    success = await stop_stream(key)
    if not success:
        raise HTTPException(status_code=404, detail=f"No active stream for {req.symbol}@{req.interval}")
    return StreamResponse(message=f"🛑 Stopped streaming for {req.symbol}@{req.interval}")

@app.post("/update", response_model=StreamResponse)
async def update_streaming(req: StreamUpdateRequest):
    old_key = (req.old_symbol.lower(), req.old_interval)
    new_key = (req.new_symbol.lower(), req.new_interval)
    if new_key in STREAMS:
        raise HTTPException(status_code=400, detail=f"Stream already running for {req.new_symbol}@{req.new_interval}")
    success = await update_stream(old_key, new_key)
    if not success:
        raise HTTPException(status_code=404, detail=f"Stream not found for {req.old_symbol}@{req.old_interval}")
    return StreamResponse(message=f"🔁 Updated stream from {req.old_symbol}@{req.old_interval} to {req.new_symbol}@{req.new_interval}")

@app.get("/streams", response_model=StreamListResponse)
async def list_active_streams():
    keys = [f"{s}@{i}" for (s, i) in STREAMS.keys()]
    return StreamListResponse(active_streams=keys)

@app.post("/start/batch", response_model=StreamListResponse)
async def batch_start_streams(reqs: list[OHLCVRequest]):
    if len(reqs) > 20:
        raise HTTPException(status_code=400, detail="Too many streams requested. Limit is 20 per batch.")
    started = []
    for req in reqs:
        key = (req.symbol.lower(), req.interval)
        if key not in STREAMS:
            await start_stream(key)
            started.append(f"{req.symbol}@{req.interval}")
    return StreamListResponse(active_streams=started)

@app.delete("/stop/all", response_model=StreamListResponse)
async def stop_all_streams(confirm: bool = Query(..., description="Confirmation required to stop all streams")):
    if not confirm:
        raise HTTPException(status_code=400, detail="Confirmation required to stop all streams")
    for key in list(STREAMS.keys()):
        await stop_stream(key)
    return StreamListResponse(active_streams=[])
