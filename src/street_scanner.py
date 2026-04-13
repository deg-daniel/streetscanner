import os
import time
import shutil
import asyncio
from pathlib import Path
from io import BytesIO
from PIL import Image

from maps_service import GoogleMapsService
from route_manager import RouteManager
from vision_analyzer import VisionAnalyzer

WAITING_TIME_GSTREET = 5

class StreetScanner:
    def __init__(self):
        api_key = os.getenv("GOOGLE_MAPS_API_KEY")
        self.maps = GoogleMapsService(api_key)
        self.route_tool = RouteManager()
        self.vision = VisionAnalyzer()
        self.threshold = 0.50
        self.image_dir = Path("./streetview_images")

    def _save_image(self,content_l,content_r,filename):
        img_l = Image.open(BytesIO(content_l))
        img_r = Image.open(BytesIO(content_r))

        width = img_l.width + img_r.width
        height = max(img_l.height, img_r.height)
        new_img = Image.new("RGB", (width, height))
        new_img.paste(img_l, (0, 0))
        new_img.paste(img_r, (img_l.width, 0))

        new_img.save(filename)

    def get_itinary(self, addr_a, addr_b):
        start = self.maps.get_coords(addr_a)
        end = self.maps.get_coords(addr_b)
        if start is None or end is None:
            return []
        print(f"{addr_a} --> {addr_b}")
        print("Fetch intinary..")
        #raw_path = self.maps.fetch_directions(start, end) # only itinary, some pins
        raw_path = self.maps.fetch_directions_fine(start, end) # use more pins
        print("Resample route..")
        pins = self.route_tool.resample(raw_path)
        #print("Snap road..")
        #pins = self.maps.snap_route(pins)
        #self.route_tool.debug_route(pins)
        return pins

    def _save_googlestreet_image(self, pin, next_pin):
        heading_route = self.route_tool.calculate_heading(pin, next_pin)
            
        # Angles à 90° pour regarder les façades
        angle_gauche = (heading_route - 90) % 360
        angle_droite = (heading_route + 90) % 360
        
        # Téléchargement des deux vues perpendiculaires
        content_l = self.maps.download_sv_image(pin[0], pin[1], angle_gauche)
        content_r = self.maps.download_sv_image(pin[0], pin[1], angle_droite)
        
        if not content_l or not content_r:
            return None

        filename = self.image_dir / f"img {pin[0]:.5f},{pin[1]:.5f}.jpg"
        self._save_image(content_l,content_r,filename)
        return filename
        
    async def process(self, addr_a, addr_b, desc=None):
        if self.image_dir.exists(): shutil.rmtree(self.image_dir)
        self.image_dir.mkdir()

        pins = self.get_itinary(addr_a, addr_b)
        
        print("Start scan!\n")
        for i, pt in enumerate(pins):
            start_time = time.time()
            pin = pins[i]
            next_pin = pins[i+1] if i < len(pins)-1 else pins[i-1]
            filename = self._save_googlestreet_image(pin, next_pin)            
            print(filename)
            score = self.vision.analyze(filename, desc) if desc else None
            res = score is not None and score >= self.threshold
            event = {
                "index": i,
                "total": len(pins),
                "score": score,
                "match": res,
                "filename": str(filename)
            }
            print(event)
            yield event
            print("throttle")
            # Throttle
            wait_time = max(0, WAITING_TIME_GSTREET - (time.time() - start_time))
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            
    async def analyze_exist_images(self, desc):
        """run with old jpg, do not streetview call again"""    
        images = sorted(self.image_dir.glob("img*.jpg"))
        for i, filename in enumerate(images):
            score = self.vision.analyze(filename, desc)
            res = score is not None and score >= self.threshold
            yield {
                "index": i,
                "total": len(images),
                "score": score,
                "match": res,
                "filename": str(filename)
            }
