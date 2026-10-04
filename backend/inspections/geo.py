import math

EARTH_RADIUS_M = 6_371_000.0
METERS_PER_DEGREE_LAT = 111_320.0


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def find_nearest(queryset, lat, lon, radius_m):
    """Return (nearest_object, distance_m) within radius_m, or (None, None)."""
    dlat = radius_m / METERS_PER_DEGREE_LAT
    dlon = radius_m / (METERS_PER_DEGREE_LAT * max(math.cos(math.radians(lat)), 0.01))
    candidates = queryset.filter(
        latitude__range=(lat - dlat, lat + dlat),
        longitude__range=(lon - dlon, lon + dlon),
    )
    best, best_d = None, None
    for obj in candidates:
        d = haversine_m(lat, lon, obj.latitude, obj.longitude)
        if d <= radius_m and (best_d is None or d < best_d):
            best, best_d = obj, d
    return best, best_d