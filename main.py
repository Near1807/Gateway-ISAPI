from fastapi import FastAPI, HTTPException, Request
import redis
import uvicorn
import xmltodict
import threading
from config import *
from library import *

app = FastAPI()
DOORS = door_set_up()

queue = redis.Redis(
    host=Redis_url,
    port=Redis_port,
    db=0,
    socket_timeout=1.0,
    socket_connect_timeout=1.0,
    retry_on_timeout=False,
    decode_responses=True
)

@app.get("/")
def home():
    return {"status": "Gateway running"}

@app.post(URL_Event_Notification)
async def notifications(request: Request):
    body = await request.body()

    if not body:
        raise HTTPException(status_code=400, detail="Empty body")

    if len(body) > Max_Body_Size:
        raise HTTPException(status_code=413, detail="Payload too large")

    data = body.decode("utf-8")

    try:
        parsed = xmltodict.parse(data)
        reader_ip = parsed["EventNotificationAlert"]["ipAddress"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid XML or missing reader IP")

    if reader_ip not in DOORS:
        raise HTTPException(status_code=403, detail="Unknown reader IP")

    try:
        queue.lpush("Rfid_Queue", data)
    except redis.TimeoutError:
        raise HTTPException(status_code=503, detail="Queue timeout")
    except redis.RedisError:
        raise HTTPException(status_code=503, detail="Queue unavailable")

    return {"status": "ok"}






if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=Uvicorn_Port)

"""
    for ip, door in DOORS.items():
        try:
            door.setup_listener()
            print
        except (ConnectionError, RuntimeError) as e:
            print(f"[WARN] {e} — poursuite du démarrage sans le lecteur d'IP {door.reader_ip}")

    threading.Thread(
        target=Gateway_Main_Loop,
        args=(Url_Serveur_PLC, queue, DOORS),
        daemon=True
    ).start()"""