from config import *
import requests
from requests.auth import HTTPDigestAuth
from opcua import Client
import xmltodict

def Request_Change_Door_State(door_state):
    """
    Change the state of the door by sending an HTTP request to the reader.
        - door_state: True to open the door, False to close it.
        - Returns: True if the request was successful, False otherwise.
    """

    url = f"http://{Reader_IP}/ISAPI/System/IO/outputs/1/trigger"

    if door_state:
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <IOPortData xmlns="http://www.isapi.org/ver20/XMLSchema">
                <outputState>high</outputState>
            </IOPortData>"""
    else:
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <IOPortData xmlns="http://www.isapi.org/ver20/XMLSchema">
                <outputState>low</outputState>
            </IOPortData>"""

    try:
        response = requests.put(
            url,
            data=xml_body.encode("utf-8"),
            headers={"Content-Type": 'application/xml; charset="UTF-8"'},
            auth=HTTPDigestAuth(Reader_User, Reader_Psw)
        )
        print("Trigger reader:", response.status_code)
        return response.ok
    except Exception as e:
        print("Erreur HTTP reader:", e)
        return False



def Request_Door_State():
    """
    Request the current state of the door by sending an HTTP request to the reader.
        - Returns: True if the door is open, False if it's closed, None if there was an error.
    """

    url = f"http://{Reader_IP}/ISAPI/System/IO/outputs/{Door_State_Output_id}/status"
    try:
        Door_State = requests.get(
            url,
            auth=HTTPDigestAuth(Reader_User, Reader_Psw),
        )
        if Door_State.ok:
            data = xmltodict.parse(Door_State.text)
            state = data["IOPortStatus"]["ioPortStatus"]
            print(f"📡 État sortie {Door_State_Output_id}: {state}")
            return state == "active"
        else:
            print("Erreur HTTP reader:", Door_State.status_code)
            return None
    except Exception as e:
        print("Erreur HTTP reader:", e)
        return None




def PLC_Polling(url_Serveur_PLC):
    """
    Poll the PLC for the state of the door and update it accordingly.
        - url_Serveur_PLC: The URL of the PLC server to connect to.
    """
    
    client = Client(url_Serveur_PLC)
    client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{client_certificate_path},{client_key_path}")
    try : 
        client.connect()
        print("Connected to PLC")
    except Exception as e:
        print("Error connecting to PLC : ", e)
        return
    

    while True :
        previous_Door_State = False
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




def NewGuidConnexion(Guid):
    """
    Handle a new connection of a tag by updating the PLC with the new Guid.
        - Guid: The Guid of the newly connected tag.
    """
    client = Client(url_Serveur_PLC)
    client.set_security_string(f"Basic256Sha256,SignAndEncrypt,{client_certificate_path},{client_key_path}")
    try : 
        client.connect()
        print("Connected to PLC")
    except Exception as e:
        print("Error connecting to PLC : ", e)
        return
    
    try :
        Guid_Node = client.get_node(Guid_NodeId)
        Guid_Node.set_value(Guid)
        print(f"New Guid {Guid} set in PLC")
    except Exception as e:
        print("Error writing Guid to PLC : ", e)