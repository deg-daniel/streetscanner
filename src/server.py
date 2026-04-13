import asyncio
import os
import sys
from multiprocessing import Process, Manager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
import uvicorn

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/streetview_images", StaticFiles(directory="streetview_images"), name="streetview_images")

# Ctrl+C work ;-)
def receive_signal(signalNumber, frame):
    print('Received:', signalNumber)
    sys.exit()
@app.on_event("startup")
async def startup_event():
    import signal
    signal.signal(signal.SIGINT, receive_signal)



@app.get("/", response_class=HTMLResponse)
def home():
    with open("static/index.html", "r") as f:
        return f.read()


def run_scanner(action, params, queue):
    try:
        from street_scanner import StreetScanner
        scanner = StreetScanner()
        
        async def task():
            if action == "getimages":
                async for event in scanner.process(params['a'], params['b']):
                    queue.put(event)
            
            elif action == "getandanalyze":
                async for event in scanner.process(params['a'], params['b'], params['desc']):
                    queue.put(event)
            
            elif action == "analyze":
                async for event in scanner.analyze_exist_images(params['desc']):
                    print(event)
                    queue.put(event)
            
            elif action == "itinary":
                pins = scanner.get_itinary(params['a'], params['b'])
                result = {
                    "itinary": [
                        [lat, lon] for lat, lon in pins
                    ]
                }
                queue.put(result)

        asyncio.run(task())
    except Exception as e:
        queue.put({"error": str(e)})

@app.websocket("/ws/{action}")
async def websocket_endpoint(websocket: WebSocket, action: str):
    if action not in ["getimages", "getandanalyze", "analyze", "itinary"]:
        await websocket.close(code=1003)
        return

    await websocket.accept()
    
    try:
        params = await websocket.receive_json()
        
        manager = Manager()
        queue = manager.Queue()
        p = Process(target=run_scanner, args=(action, params, queue))
        p.start()

        loop = asyncio.get_event_loop()
        
        while p.is_alive() or not queue.empty():
            try:
                # check non-bloquant de la queue
                event = await loop.run_in_executor(None, lambda: queue.get(timeout=0.2))
                
                if isinstance(event, dict) and "error" in event:
                    await websocket.send_json(event)
                    break
                    
                await websocket.send_json(event)
            except:
                # queue empty, check if process is dead
                await asyncio.sleep(0.5)
                continue

        p.join()
        await websocket.close()

    except ValidationError as e:
        await websocket.send_json({"error": "missing_parameters", "details": e.errors()})
        await websocket.close()
    except WebSocketDisconnect:
        if p.is_alive():
            p.terminate()
        p.join()
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        if p.is_alive():
            p.terminate()
        p.join()
        await websocket.close()
        
if __name__ == "__main__":
    if not os.getenv("GOOGLE_MAPS_API_KEY"):
        print("\n⚠️⚠️ set GOOGLE_MAPS_API_KEY before run ⚠️⚠️\n")
        sys.exit(1)

    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002, reload=False)
