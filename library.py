from fastapi import FastAPI, HTTPException, Request
import redis
import uvicorn
import xmltodict
import threading
from config import *
from time import sleep
from opcua.ua.uaerrors import UaStatusCodeError
from opcua import Client
from doors import Door


def Gateway_Main_Loop(url_Serveur_PLC,queue,DOORS):
    while True:
        try:
            client = Client(url_Serveur_PLC, timeout=Opcua_Timeout)
            client.set_security_string(
                f"Basic256Sha256,SignAndEncrypt,{Client_certificate_path},{Client_key_path}"
            )
            client.connect()
            print("Connected to PLC")
        except Exception as e:
            print("Error connecting to PLC:", e)
            sleep(Reconnect_Time_PLC)
            continue

        while True:
            try:
                Rfid_task = queue.lpop("Rfid_Queue")

                if Rfid_task:
                    parsed = xmltodict.parse(Rfid_task)

                    alert = parsed["EventNotificationAlert"]
                    event = alert["AccessControllerEvent"]

                    reader_ip = alert["ipAddress"]
                    door = DOORS[reader_ip]
                    guid = event["cardNo"]

                    if reader_has_opened_autonomous(event):
                        print(f"[{reader_ip}] Reader autonome a déjà ouvert | GUID={guid}")
                    else:
                        print(f"[{reader_ip}] Envoi GUID au PLC | GUID={guid}")
                        door.new_guid_connexion(client, guid)

                for reader_ip, door in DOORS.items():
                    door_state = client.get_node(door.door_node_id).get_value()

                    if door_state != door.previous_door_state:
                        door.request_change_door_state(door_state)
                        door.previous_door_state = door_state

                    if door.check_state_timer >= Check_State_Time:
                        door.check_state_timer = 0
                        door.request_door_state(client)

                    door.process_flags(client, Sleep_Time)
                    door.check_state_timer += Sleep_Time

                sleep(Sleep_Time)

            except UaStatusCodeError as e:
                print("Connexion PLC perdue, reconnexion...", e)
                try:
                    client.disconnect()
                except:
                    pass
                break   # important : sortir du while interne pour reconnecter

            except Exception as e:
                print("Erreur non critique:", e)


def reader_has_opened_autonomous(event: dict) -> bool:
    """
    Retourne True si la notif indique que le reader a déjà accordé/ouvert.
    À adapter avec les vrais subEventType observés sur TON lecteur.
    """

    sub_event = event.get("subEventType")


    access_granted = 1 

    if sub_event == access_granted:
        return True
    else :
        return False



def door_set_up():
    DOORS = {
        "127.0.0.1": Door(
            reader_id=1,
            name="Door_1",
            reader_ip="127.0.0.1",
            reader_port=80,
            reader_user="admin",
            reader_psw="admin",
            door_state_output_id=1,
            guid_node_id="ns=1;s=Guid_Tag",
            door_node_id="ns=2;s=Door_Tag",
            door_state_node_id="ns=3;s=Door_State_Tag",
            guid_flag_node_id="ns=1;s=Guid_Flag_Tag",
            door_state_flag_node_id="ns=3;s=Door_State_Flag_Tag"
        )
    }
    return DOORS