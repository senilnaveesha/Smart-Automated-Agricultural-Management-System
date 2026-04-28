import random


DISEASE_LABELS = [
    "brown_blight",
    "gray_blight",
    "white_spot",
]


def classify_image_fake(image_path: str) -> tuple[str, float]:
    """
    Temporary classifier for simulation.
    Later this can be replaced by YOLO output.

    Returns:
        (label, confidence)
    """

    # Adjust weights however you like for demo realism
    label = random.choices(
        population=["healthy", "brown_blight", "gray_blight", "white_spot"],
        weights=[45, 25, 18, 12],
        k=1
    )[0]

    confidence = round(random.uniform(0.75, 0.98), 2)

    return label, confidence


def process_scan_point(point, image_path):
    """
    Core processing logic.

    Current mode:
        Fake disease classification for simulation

    Future mode:
        Replace classify_image_fake() with YOLO inference,
        but keep the returned dictionary structure the same.
    """

    lat, lon = point

    label, confidence = classify_image_fake(image_path)

    status = "healthy" if label == "healthy" else "diseased"

    return {
        "lat": lat,
        "lon": lon,
        "label": label,
        "status": status,
        "confidence": confidence,
        "image": image_path
    }