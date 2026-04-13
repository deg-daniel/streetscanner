import requests
import polyline
from math import radians, cos, sin, sqrt, atan2

class GoogleMapsService:
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = requests.Session()

    @staticmethod
    def haversine(p1, p2):
        R = 6371000
        lat1, lon1, lat2, lon2 = map(radians, [p1[0], p1[1], p2[0], p2[1]])
        a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    def get_coords(self, address):
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        r = self.session.get(url, params={"address": address, "key": self.api_key})
        data = r.json()
        return (data["results"][0]["geometry"]["location"]["lat"], 
                data["results"][0]["geometry"]["location"]["lng"]) if data["status"] == "OK" else None

    def fetch_directions(self, origin, dest):
        url = "https://maps.googleapis.com/maps/api/directions/json"
        params = {"origin": f"{origin[0]},{origin[1]}", "destination": f"{dest[0]},{dest[1]}", 
                  "mode": "walking", "key": self.api_key}
        r = self.session.get(url, params=params)
        return polyline.decode(r.json()["routes"][0]["overview_polyline"]["points"]) if r.json()["status"] == "OK" else []

    def fetch_directions_fine(self, origin, dest):
        url = "https://maps.googleapis.com/maps/api/directions/json"

        params = {
            "origin": f"{origin[0]},{origin[1]}",
            "destination": f"{dest[0]},{dest[1]}",
            "mode": "walking",
            "key": self.api_key
        }

        r = self.session.get(url, params=params)
        data = r.json()

        if data.get("status") != "OK":
            return []

        route = data["routes"][0]

        points = []

        # on prend toutes les steps = plus précis que overview_polyline
        for leg in route.get("legs", []):
            for step in leg.get("steps", []):
                poly = step.get("polyline", {}).get("points")
                if poly:
                    points.extend(polyline.decode(poly))

        return points

    def snap_route(self, points, length_tolerance=0.3):
        if not points:
            return points

        BATCH_SIZE = 100
        snapped_all = []

        try:
            for i in range(0, len(points), BATCH_SIZE):
                chunk = points[i:i + BATCH_SIZE]

                path = "|".join([f"{lat},{lng}" for lat, lng in chunk])

                url = "https://roads.googleapis.com/v1/snapToRoads"
                params = {
                    "path": path,
                    "interpolate": "true",
                    "key": self.api_key
                }
                r = self.session.get(url, params=params)
                data = r.json()

                if "snappedPoints" not in data:
                    print("[snap_route] fallback: no snappedPoints")
                    return points

                for p in data["snappedPoints"]:
                    loc = p["location"]
                    snapped_all.append((loc["latitude"], loc["longitude"]))

        except Exception as e:
            print(f"[snap_route] exception: {e}")
            return points

        if len(snapped_all) < len(points) * 0.7:
            print(f"[snap_route] fallback: too few snapped points: {len(snapped_all)} < {len(points)}")
            return points

        # --- helper local ---
        def path_length(route):
            return sum(
                self.haversine(route[i - 1], route[i])
                for i in range(1, len(route))
            )

        original_len = path_length(points)
        snapped_len = path_length(snapped_all)

        ratio = abs(snapped_len - original_len) / original_len

        # --- sanity check global ---
        if ratio > length_tolerance:
            print(f"[snap_route] reject snap. Length ratio diff: {ratio:.3f}")
            return points

        return snapped_all
        
    def download_sv_image(self, lat, lng, heading):
        url = "https://maps.googleapis.com/maps/api/streetview"
        params = {"size": "640x640", "location": f"{lat},{lng}", "heading": heading, "key": self.api_key}
        r = self.session.get(url, params=params)
        if r.status_code == 200:
            return r.content
        return None