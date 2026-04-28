import os
import random

IMAGE_FOLDER = "simulation/test_images"


def get_test_image():
    files = [f for f in os.listdir(IMAGE_FOLDER) if f.lower().endswith((".jpg", ".png"))]

    if not files:
        raise Exception("❌ No test images found in simulation/test_images")

    return os.path.join(IMAGE_FOLDER, random.choice(files))