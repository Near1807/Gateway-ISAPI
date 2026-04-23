import requests
from requests.auth import HTTPDigestAuth
import xmltodict


class Door:
    """
    Représente une porte contrôlée par un lecteur RFID Hikvision et un PLC OPC-UA.
    
    Gère :
        - La communication HTTP avec le lecteur physique (ouverture/fermeture, état)
        - La mise à jour des nodes OPC-UA du PLC (GUID, état porte)
        - Les flags OPC-UA avec reset automatique par timer
    """

    def __init__(self, name, reader_ip, reader_user, reader_psw, door_state_output_id,
                 guid_node_id, door_node_id, door_state_node_id,
                 guid_flag_node_id, door_state_flag_node_id,
                 guid_flag_reset_time=5, door_state_flag_reset_time=10):
        """
        Args:
            name                        : Nom de la porte (ex: "Door_1")
            reader_ip                   : IP du lecteur RFID
            reader_user                 : Utilisateur HTTP du lecteur
            reader_psw                  : Mot de passe HTTP du lecteur
            door_state_output_id        : ID de la sortie IO du lecteur pour l'état de la porte

            guid_node_id                : NodeId OPC-UA du GUID du badge
            door_node_id                : NodeId OPC-UA de la commande d'ouverture porte (lu depuis le PLC)
            door_state_node_id          : NodeId OPC-UA de l'état physique de la porte
            guid_flag_node_id           : NodeId OPC-UA du flag GUID
            door_state_flag_node_id     : NodeId OPC-UA du flag état porte

            guid_flag_reset_time        : Temps en secondes avant reset du flag GUID (défaut: 5)
            door_state_flag_reset_time  : Temps en secondes avant reset du flag état porte (défaut: 10)
        """

        # --- Infos lecteur ---
        self.name = name
        self.reader_ip = reader_ip
        self.reader_user = reader_user
        self.reader_psw = reader_psw
        self.door_state_output_id = door_state_output_id

        # --- Nodes PLC ---
        self.guid_node_id = guid_node_id
        self.door_node_id = door_node_id
        self.door_state_node_id = door_state_node_id
        self.guid_flag_node_id = guid_flag_node_id
        self.door_state_flag_node_id = door_state_flag_node_id

        # --- State runtime (évolue pendant l'exécution) ---
        self.previous_door_state = False
        self.check_state_timer = 0

        # --- Flags OPC-UA ---
        # Chaque flag a un NodeId PLC, une valeur courante, un timer et un temps de reset
        self.flags = {
            "Guid_Flag": {
                "NodeId": self.guid_flag_node_id,
                "Value": False,
                "Timer": 0,
                "Reset_Timer": guid_flag_reset_time
            },
            "Door_State_Flag": {
                "NodeId": self.door_state_flag_node_id,
                "Value": False,
                "Timer": 0,
                "Reset_Timer": door_state_flag_reset_time
            }
        }


    def new_guid_connexion(self, client, guid):
        """
        Appelé quand un badge est scanné.
        Écrit le GUID dans le node PLC correspondant et lève le flag GUID.

        Args:
            client  : Client OPC-UA connecté
            guid    : GUID du badge scanné (string)
        """
        self.change_node_value(client, self.guid_node_id, guid, "Guid_Flag")
        print(f"[{self.name}] New Guid {guid} set in PLC")


    def request_change_door_state(self, state):
        """
        Envoie une requête HTTP au lecteur pour ouvrir ou fermer la porte.

        Args:
            state   : True pour ouvrir, False pour fermer
        Returns:
            True si la requête a réussi, False sinon
        """
        url = f"http://{self.reader_ip}/ISAPI/System/IO/outputs/1/trigger"
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
            <IOPortData xmlns="http://www.isapi.org/ver20/XMLSchema">
                <outputState>{"high" if state else "low"}</outputState>
            </IOPortData>"""
        try:
            response = requests.put(
                url,
                data=xml_body.encode("utf-8"),
                headers={"Content-Type": 'application/xml; charset="UTF-8"'},
                auth=HTTPDigestAuth(self.reader_user, self.reader_psw)
            )
            print(f"[{self.name}] Trigger reader: {response.status_code}")
            return response.ok
        except Exception as e:
            print(f"[{self.name}] Erreur HTTP reader: {e}")
            return False


    def request_door_state(self, client):
        """
        Interroge le lecteur pour connaître l'état physique actuel de la porte
        et met à jour le node OPC-UA correspondant.

        Args:
            client  : Client OPC-UA connecté
        """
        url = f"http://{self.reader_ip}/ISAPI/System/IO/outputs/{self.door_state_output_id}/status"
        try:
            response = requests.get(url, auth=HTTPDigestAuth(self.reader_user, self.reader_psw))
            if response.ok:
                data = xmltodict.parse(response.text)
                state = data["IOPortStatus"]["ioPortStatus"]
                self.change_node_value(client, self.door_state_node_id, state == "active", "Door_State_Flag")
                print(f"[{self.name}] Door state: {state}")
            else:
                print(f"[{self.name}] Erreur HTTP reader: {response.status_code}")
        except Exception as e:
            print(f"[{self.name}] Erreur HTTP reader: {e}")


    def change_node_value(self, client, node_id, value, flag_name):
        """
        Écrit une valeur dans un node OPC-UA et lève le flag associé.
        Le flag est mis à True dans le PLC et son timer est remis à zéro.

        Args:
            client      : Client OPC-UA connecté
            node_id     : NodeId OPC-UA à modifier
            value       : Nouvelle valeur à écrire
            flag_name   : Clé du flag dans self.flags à lever
        """
        node = client.get_node(node_id)
        node.set_value(value)
        print(f"[{self.name}] Node {node_id} → {value}")

        flag = self.flags[flag_name]
        flag_node = client.get_node(flag["NodeId"])
        flag_node.set_value(True)
        flag["Value"] = True
        flag["Timer"] = 0
        print(f"[{self.name}] Flag {flag_name} set to True")


    def process_flags(self, client, sleep_time):
        """
        À appeler à chaque tour de boucle principale.
        Incrémente le timer de chaque flag actif et remet à False
        les flags qui ont atteint leur Reset_Timer (dans le PLC et en local).

        Args:
            client      : Client OPC-UA connecté
            sleep_time  : Durée du sleep de la boucle principale (en secondes)
        """
        for flag_name, flag in self.flags.items():
            if flag["Value"]:
                flag["Timer"] += sleep_time
                if flag["Timer"] >= flag["Reset_Timer"]:
                    flag["Value"] = False
                    flag["Timer"] = 0
                    node = client.get_node(flag["NodeId"])
                    node.set_value(False)
                    print(f"[{self.name}] Flag {flag_name} reset")