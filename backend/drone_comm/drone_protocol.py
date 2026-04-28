import json


def make_path_start(count: int) -> dict:
    return {"type": "path_start", "count": count}


def make_path_point(index: int, lat: float, lon: float) -> dict:
    return {
        "type": "path_point",
        "index": index,
        "lat": lat,
        "lon": lon,
    }


def make_path_end() -> dict:
    return {"type": "path_end"}


def make_start_scan() -> dict:
    return {"type": "start_scan"}


def make_stop_scan() -> dict:
    return {"type": "stop_scan"}


def make_manual_control(throttle: float, yaw: float, pitch: float, roll: float) -> dict:
    return {
        "type": "move",
        "throttle": float(throttle),
        "yaw": float(yaw),
        "pitch": float(pitch),
        "roll": float(roll),
    }


def make_goto_command(lat: float, lon: float) -> dict:
    return {
        "type": "goto",
        "lat": float(lat),
        "lon": float(lon),
    }


def make_stop_command() -> dict:
    return {"type": "stop"}


def make_emergency_stop() -> dict:
    return {"type": "emergency_stop"}


def encode_packet(packet: dict) -> bytes:
    return json.dumps(packet).encode("utf-8")