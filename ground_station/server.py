from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional

app = FastAPI(title="SmartFarm Ground Station")

# In-memory latest snapshots (good for prototype)
LATEST: Dict[str, Dict[str, Any]] = {}

class SensorPayload(BaseModel):
    # Current working sensors
    soil1_raw: int = Field(..., ge=0, le=4095)
    soil2_raw: int = Field(..., ge=0, le=4095)
    rain: bool
    pump_on: bool
    ts: int  # seconds from ESP32 (millis()/1000 is OK for prototype)

    # Optional future fields (when DHT works)
    temperature: Optional[float] = None
    humidity: Optional[float] = Field(default=None, ge=0, le=100)

@app.post("/api/v1/nodes/{node_id}/sensors")
def ingest(node_id: str, payload: SensorPayload):
    LATEST[node_id] = {
        "node_id": node_id,

        # raw soil readings for now
        "soil1_raw": payload.soil1_raw,
        "soil2_raw": payload.soil2_raw,

        # optional future fields
        "temperature": payload.temperature,
        "humidity": payload.humidity,

        "rain": payload.rain,
        "pump_on": payload.pump_on,

        "device_ts": payload.ts,
        "received_at": int(datetime.utcnow().timestamp()),
        "source": "wifi",
    }
    return {"ok": True}

@app.get("/api/v1/nodes/{node_id}/latest")
def latest(node_id: str):
    if node_id not in LATEST:
        raise HTTPException(status_code=404, detail="No data yet for this node")
    return LATEST[node_id]