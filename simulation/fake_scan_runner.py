import time
import json

from simulation.fake_camera import get_test_image
from backend.data_pipeline import process_scan_point


def run_fake_scan(path, callback=None, delay=0.05):
    """
    Simulate scanning the field.

    path: list of (lat, lon)
    callback: function to send results back (UI / map)
    delay: time between points (simulate movement)
    """

    print("🚁 Starting FAKE scan...")

    results = []

    for i, point in enumerate(path):
        lat, lon = point

        # 📸 Get fake image
        image = get_test_image()

        # 🧠 Process (YOLO later)
        result = process_scan_point(point, image)

        results.append(result)

        print(f"📍 Point {i+1}/{len(path)} processed:", result)

        # 🔥 Send to UI (optional)
        if callback:
            callback(result)

        time.sleep(delay)

    print("✅ Fake scan completed")

    return results