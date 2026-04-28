from shapely.geometry import Polygon, LineString


def generate_grid_path(coords, spacing=0.00002, sample_step=0.00002):
    """
    coords: list of [lat, lon]
    spacing: distance between scan rows
    sample_step: distance between scan points along each row
    """

    if not coords or len(coords) < 3:
        return []

    # Convert [lat, lon] -> (lon, lat) for Shapely
    polygon_points = [(lon, lat) for lat, lon in coords]
    poly = Polygon(polygon_points)

    if not poly.is_valid:
        poly = poly.buffer(0)

    minx, miny, maxx, maxy = poly.bounds  # x=lon, y=lat

    lines = []
    y = miny

    # Generate horizontal sweep lines across latitude
    while y <= maxy:
        line = LineString([(minx, y), (maxx, y)])
        intersection = line.intersection(poly)

        if not intersection.is_empty:
            if intersection.geom_type == "LineString":
                lines.append(intersection)
            elif intersection.geom_type == "MultiLineString":
                lines.extend(list(intersection.geoms))

        y += spacing

    path = []
    reverse = False

    for seg in lines:
        segment_points = sample_line(seg, sample_step)

        if reverse:
            segment_points.reverse()

        path.extend(segment_points)
        reverse = not reverse

    return path


def sample_line(line, step):
    """
    Sample multiple points along a LineString.
    Returns points as [lat, lon] for the rest of your app.
    """
    length = line.length

    if length == 0:
        x, y = line.coords[0]
        return [[y, x]]

    points = []
    distance = 0.0

    while distance < length:
        p = line.interpolate(distance)
        points.append([p.y, p.x])  # convert back to [lat, lon]
        distance += step

    # Always include final endpoint
    p = line.interpolate(length)
    points.append([p.y, p.x])

    return points