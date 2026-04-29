import requests
from requests.auth import HTTPDigestAuth
from config import *
from doors import *
from library import *
import time

# Vérifie que le serveur FastAPI est bien up
try:
    r = requests.get(f"http://{Uvicorn_Host}:{Uvicorn_Port}/")
    print(f"Serveur OK : {r.status_code}")
except Exception as e:
    print(f"Serveur pas encore démarré : {e}")
    exit()

doors = door_set_up()
for ip, door in doors.items():
    result = door.setup_listener()
    print(f"[{ip}] Setup listener: {'OK ✓' if result else 'FAILED ✗'}")