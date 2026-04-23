from fastapi import FastAPI, Request
import redis
import uvicorn
import xmltodict
from library import *
import threading
from config import *
from time import sleep

app = FastAPI()
queue = redis.from_url(Redis_url)

#------------------- Flask pour les notifications du lecteur ------------------#
@app.post("/")
def home():
    return "Hello World !"

@app.post(URL_Event_Notification)
async def notifications(request: Request):
    data = await request.body()
    queue.lpush(Guid_Request_Queue, data)
    return
    

###-------------------Boucle Principale pour le traitement des requêtes------------------#
def PLC_Polling(url_Serveur_PLC):
    """
    Poll the PLC for the state of the door and update it accordingly.
        - url_Serveur_PLC: The URL of the PLC server to connect to.
    """
    
    client = Client(url_Serveur_PLC)
    client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{Client_certificate_path},{Client_key_path}")
    try : 
        client.connect()
        print("Connected to PLC")
    except Exception as e:
        print("Error connecting to PLC : ", e)
        return
    
    previous_Door_State = False
    check_state_timer = 0
    while True :
        #---Gestion de la queue des connexions---#
        Guid_task = queue.lpop(Guid_Request_Queue)
        if Guid_task :
            Guid = xmltodict.parse(Guid_task)["TagNotification"]["TagInfo"]["GUID"]
            NewGuidConnexion(client, Guid)

        #---Gestion de l'ouverture/fermeture de la porte---#
        try :
            Door= client.get_node(Door_NodeId)
            Door_State = Door.get_value()
            if Door_State != previous_Door_State :
                if Door_State == True :
                    Request_Change_Door_State(True)
                else :
                    Request_Change_Door_State(False)

                print(f"New door State {Door_State}")
                previous_Door_State = Door_State
        except Exception as e:
            print("Error reading Tag1 : ", e)


        #---Check de l'état de la porte tous les x temps---#    
        if check_state_timer >= check_state_time :
            check_state_timer = 0
            Request_Door_State()


        sleep(sleep_time) and check_state_timer += sleep_time




if __name__ == "__main__":
    threading.Thread(target=PLC_Polling, args=(Url_Serveur_PLC,), daemon=True).start()
    uvicorn.run(app, host=Uvicorn_Host, port=Uvicorn_Port)