from fastapi import FastAPI, Request
import redis
import uvicorn
import xmltodict
import threading
from config import *
from time import sleep
from opcua.ua.uaerrors import UaStatusCodeError
from opcua import Client

app = FastAPI()
queue = redis.from_url(Redis_url)

#------------------- Flask pour les notifications du lecteur ------------------#
@app.post("/")
def home():
    return "Hello World !"

@app.post(URL_Event_Notification)
async def notifications(request: Request):
    data = await request.body()
    queue.lpush("Rfid_Queue", data)
    return {"status": "ok"}

###-------------------Boucle Principale pour le traitement des requêtes------------------#
def Gateway_Main_Loop(url_Serveur_PLC):
    """
    Boucle principale du système de contrôle d'accès.
    Gère la connexion au PLC (avec reconnexion automatique) et traite :
        - La queue Redis des badges scannés (GUID) pour mise à jour du PLC
        - L'état de la porte via le PLC et actionnement du lecteur
        - La vérification périodique de l'état physique de la porte
    """
    while True:
        try:
            client = Client(url_Serveur_PLC)
            client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{Client_certificate_path},{Client_key_path}")
            client.connect()
            print("Connected to PLC")
        except Exception as e:
            print("Error connecting to PLC:", e)
            sleep(Reconnect_Time_PLC)
            continue

        plc_lost = False

        while not plc_lost:
            try:
                #---Gestion de la queue des connexions---#
                Rfid_task = queue.lpop("Rfid_Queue")
                if Rfid_task:
                    parsed = xmltodict.parse(Rfid_task)
                    reader_ip = parsed["EventNotificationAlert"]["ipAddress"]
                    door = DOORS[reader_ip]
                    guid = parsed["EventNotificationAlert"]["AccessControllerEvent"]["cardNo"]
                    door.new_guid_connexion(client, guid)
                

                for reader_ip, door in DOORS.items():
                    #---Gestion de l'ouverture/fermeture de la porte---#
                    door_state = client.get_node(door.door_node_id).get_value()
                    if door_state != door.previous_door_state:
                        door.request_change_door_state(door_state)
                        door.previous_door_state = door_state


                    #---Gestion des flags---#
                    if door.check_state_timer >= Check_State_Time:
                        door.check_state_timer = 0
                        door.request_door_state(client)

                    door.process_flags(client, Sleep_Time)
                    door.check_state_timer += Sleep_Time
                sleep(Sleep_Time)

            #---Gestion de la reconnexion en cas de perte de connexion avec le PLC---#
            except UaStatusCodeError as e:
                print("Connexion PLC perdue, reconnexion...", e)
                client.disconnect()
                plc_lost = True

            except Exception as e:
                print("Erreur non critique:", e)
        
if __name__ == "__main__":
    threading.Thread(target=Gateway_Main_Loop, args=(Url_Serveur_PLC,), daemon=True).start()
    uvicorn.run(app, host=Uvicorn_Host, port=Uvicorn_Port)