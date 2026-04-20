from shapely.geometry import Polygon, LineString


def generate_grid_path(coords, spacing=0.00002):
    """
    coords: list of [lat, lon]
    spacing: distance between scan lines
    """

    # Convert to shapely polygon
    poly = Polygon(coords)

    minx, miny, maxx, maxy = poly.bounds

    lines = []
    y = miny

    # Generate horizontal lines
    while y <= maxy:
        line = LineString([(minx, y), (maxx, y)])
        intersection = line.intersection(poly)

        if not intersection.is_empty:
            lines.append(intersection)

        y += spacing

    # Convert to path (zig-zag)
    path = []
    reverse = False

    for line in lines:
        # 🔥 FIX HERE
        if line.geom_type == 'MultiLineString':
            segments = list(line.geoms)
        else:
            segments = [line]

        for seg in segments:
            coords_line = list(seg.coords)

            if reverse:
                coords_line.reverse()

            path.extend(coords_line)
            reverse = not reverse

    return path