import math
from math import radians, cos, sin, sqrt, atan2

class RouteManager:
    @staticmethod
    def haversine(p1, p2):
        R = 6371000
        lat1, lon1, lat2, lon2 = map(radians, [p1[0], p1[1], p2[0], p2[1]])
        a = sin((lat2-lat1)/2)**2 + cos(lat1)*cos(lat2)*sin((lon2-lon1)/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    def interpolate(self, p1, p2, t):
        # interpolation géo simple mais propre enough à cette échelle
        return (
            p1[0] + (p2[0] - p1[0]) * t,
            p1[1] + (p2[1] - p1[1]) * t
        )

    def resample(self, route, step=10):
        if not route:
            return []

        new_route = [route[0]]
        last = route[0]
        acc = 0.0

        for i in range(1, len(route)):
            cur = route[i]
            d = self.haversine(last, cur)

            if d == 0:
                continue

            while acc + d >= step:
                remaining = step - acc
                t = remaining / d

                new_point = self.interpolate(last, cur, t)
                new_route.append(new_point)

                # on "avance" sur le segment
                last = new_point
                d = self.haversine(last, cur)
                acc = 0.0

            acc += d
            last = cur

        return new_route
    
        
    @staticmethod
    def calculate_heading(p1, p2):
        lat1, lon1, lat2, lon2 = map(radians, [p1[0], p1[1], p2[0], p2[1]])
        x = sin(lon2-lon1) * cos(lat2)
        y = cos(lat1)*sin(lat2) - sin(lat1)*cos(lat2)*cos(lon2-lon1)
        return (math.degrees(atan2(x, y)) + 360) % 360
        
    def debug_route(self, route):
        if not route or len(route) < 2:
            print("route empty or too short")
            return

        distances = []

        for i in range(1, len(route)):
            d = self.haversine(route[i-1], route[i])
            distances.append(d)

            print(f"{i-1}->{i} : {d:.2f} m")

            if d == 0:
                print("  DUPLICATE POINT")
            elif d > 50:
                print("  BIG GAP")

        print("--- summary ---")
        print("points:", len(route))
        print("min:", min(distances))
        print("max:", max(distances))
        print("avg:", sum(distances)/len(distances))