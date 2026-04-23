from config import *
import requests #recherches files d'attentes et burst
from requests.auth import HTTPDigestAuth
from opcua import *
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




def NewGuidConnexion(client, Guid):
    """
    Handle a new connection of a tag by updating the PLC with the new Guid.
        - Guid: The Guid of the newly connected tag.
    """
    try :
        Guid_Node = client.get_node(Guid_NodeId)
        Guid_Node.set_value(Guid)
        print(f"New Guid {Guid} set in PLC")
    except Exception as e:
        print("Error writing Guid to PLC : ", e)