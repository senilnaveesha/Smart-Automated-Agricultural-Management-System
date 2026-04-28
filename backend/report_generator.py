from collections import Counter


def classify_field_risk(diseased_percent: float) -> str:
    if diseased_percent < 20:
        return "Healthy"
    elif diseased_percent < 50:
        return "Moderate Risk"
    return "High Risk"


def prettify_disease_name(name: str) -> str:
    if not name or name == "None":
        return "None"
    return name.replace("_", " ").title()


def collect_disease_examples(scan_results: list[dict]) -> dict:
    """
    Collect one representative image path for each detected disease.
    Uses the first valid image found for each disease label.
    """
    examples = {}

    for point in scan_results:
        label = point.get("label")
        image = point.get("image")

        if not label or label == "healthy":
            continue

        if label not in examples and image:
            examples[label] = image

    return examples


def generate_disease_summary(scan_results: list[dict]) -> dict:
    total_points = len(scan_results)

    if total_points == 0:
        return {
            "total_points": 0,
            "healthy_count": 0,
            "diseased_count": 0,
            "healthy_percent": 0.0,
            "diseased_percent": 0.0,
            "overall_field_health": "Unknown",
            "disease_counts": {},
            "detected_diseases": [],
            "disease_examples": {},
            "most_common_disease": "None",
        }

    healthy_count = sum(1 for p in scan_results if p.get("status") == "healthy")
    diseased_count = sum(1 for p in scan_results if p.get("status") == "diseased")

    healthy_percent = round((healthy_count / total_points) * 100, 2)
    diseased_percent = round((diseased_count / total_points) * 100, 2)

    disease_labels = [
        p.get("label")
        for p in scan_results
        if p.get("label") and p.get("label") != "healthy"
    ]

    disease_counts = dict(Counter(disease_labels))
    detected_diseases = list(disease_counts.keys())
    disease_examples = collect_disease_examples(scan_results)

    if disease_counts:
        most_common_disease = max(disease_counts, key=disease_counts.get)
    else:
        most_common_disease = "None"

    return {
        "total_points": total_points,
        "healthy_count": healthy_count,
        "diseased_count": diseased_count,
        "healthy_percent": healthy_percent,
        "diseased_percent": diseased_percent,
        "overall_field_health": classify_field_risk(diseased_percent),
        "disease_counts": disease_counts,
        "detected_diseases": detected_diseases,
        "disease_examples": disease_examples,
        "most_common_disease": most_common_disease,
    }


def format_summary_for_display(summary: dict) -> str:
    lines = [
        "Disease Monitoring Report",
        "",
        f"Total scanned points: {summary['total_points']}",
        f"Healthy: {summary['healthy_count']} ({summary['healthy_percent']}%)",
        f"Diseased: {summary['diseased_count']} ({summary['diseased_percent']}%)",
        f"Overall Field Health: {summary['overall_field_health']}",
        "",
        "Detected Disease Types:",
    ]

    if summary["disease_counts"]:
        for disease, count in summary["disease_counts"].items():
            example_image = summary.get("disease_examples", {}).get(disease, "No image")
            lines.append(
                f"- {prettify_disease_name(disease)}: {count} | Example Image: {example_image}"
            )
    else:
        lines.append("- No disease detected")

    lines.extend([
        "",
        f"Most Common Disease: {prettify_disease_name(summary['most_common_disease'])}"
    ])

    return "\n".join(lines)