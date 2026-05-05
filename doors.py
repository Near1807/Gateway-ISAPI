import requests
from requests.auth import HTTPDigestAuth
from config import *
from opcua import *
import os
from datetime import datetime

#================================================================================#
#    Classe Door - Driver complet lecteur Hikvision + intégration industrielle   #
#================================================================================#

class Door:
    """
    Classe représentant une porte physique contrôlée par un lecteur Hikvision.

    Cette classe encapsule :
    - API HTTP ISAPI (contrôle matériel)
    - Gestion RFID
    - Capture vidéo/image
    - Configuration réseau / événements
    - Interface indirecte avec PLC (via NodeIds)
    """


    def __init__(self,reader_id, name, reader_ip,reader_port, reader_user, reader_psw, door_state_output_id,
                 guid_node_id, door_node_id, door_state_node_id,
                 guid_flag_node_id, door_state_flag_node_id,
                 guid_flag_reset_time=5, door_state_flag_reset_time=10):
        """
        Initialise la porte avec tous ses paramètres.

        ------------------------------------------------------------------------
        PARAMÈTRES LECTEUR
        ------------------------------------------------------------------------
        reader_id      : identifiant interne (logique)
        name           : nom humain (logs, debug)
        reader_ip      : IP du device
        reader_port    : port HTTP (souvent 80)
        reader_user    : login HTTP
        reader_psw     : mot de passe HTTP
        door_state_output_id : ID IO physique (optionnel selon usage)

        ------------------------------------------------------------------------
        PARAMÈTRES OPC UA (liaison PLC)
        ------------------------------------------------------------------------
        guid_node_id              : badge lu
        door_node_id              : commande ouverture
        door_state_node_id        : état physique porte
        guid_flag_node_id         : flag trigger GUID
        door_state_flag_node_id   : flag trigger état porte

        ------------------------------------------------------------------------
        FLAGS
        ------------------------------------------------------------------------
        Les flags sont des booléens envoyés au PLC avec reset automatique.
        Pattern classique industriel :

            SET flag → PLC lit → RESET automatique après X secondes

        ------------------------------------------------------------------------
        STATE RUNTIME
        ------------------------------------------------------------------------
        previous_door_state : utilisé pour détecter changement d’état
        check_state_timer   : utilisé pour polling régulier

        ------------------------------------------------------------------------
        ⚠️ IMPORTANT
        ------------------------------------------------------------------------
        Cette méthode ne fait AUCUN appel réseau.
        Elle prépare uniquement l'objet.
        """

        # ========================
        # CONFIGURATION LECTEUR
        # ========================
        self.reader_id = reader_id
        self.name = name
        self.reader_ip = reader_ip
        self.reader_port = reader_port
        self.reader_user = reader_user
        self.reader_psw = reader_psw
        self.door_state_output_id = door_state_output_id

        # ID utilisé dans la config des callbacks Hikvision        
        self.host_id = 1

        # ========================
        # OPC UA
        # ========================
        self.guid_node_id = guid_node_id
        self.door_node_id = door_node_id
        self.door_state_node_id = door_state_node_id
        self.guid_flag_node_id = guid_flag_node_id
        self.door_state_flag_node_id = door_state_flag_node_id

        # ========================
        # RUNTIME
        # ========================
        self.previous_door_state = False
        self.check_state_timer = 0

        # ========================
        # FLAGS PLC
        # ========================
        """
        NodeId      : Identifiant du noeud dans le PLC
        Value       : Value stoquée dans le Node
        Timer       : Timer personnalisé du flag (sert a la gestion de la durée d'allumage d'un flag)
        Reset_Timer : Durée d'allumage du flag avant extinction (Temps customisé ou door_state_flag_reset_time)
        """
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

# ==============================================================================
# CONTRÔLE PORTE
# ==============================================================================

    def open_door(self) -> bool:
        """
        Déclenche une ouverture temporaire.

        IMPORTANT :
        - dépend de openDuration configuré dans le device
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/RemoteControl/door/1"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        payload = """<?xml version="1.0" encoding="UTF-8"?>
        <RemoteControlDoor xmlns="http://www.isapi.org/ver20/XMLSchema">
            <cmd>open</cmd>
        </RemoteControlDoor>"""

        try:
            resp = requests.put(
                url,
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/xml; charset=UTF-8"},
                auth=auth,
                timeout=Timeout,
            )

            print(f"[{self.name}] HTTP {resp.status_code}")
            print(resp.text)

            if resp.ok:
                print(f"[{self.name}] Porte ouverte ✓")
                return True

            return False

        except Exception as e:
            print(f"[{self.name}] Erreur HTTP open: {e}")
            return False


    def close_door(self) -> bool:
        """
        Force la fermeture immédiate de la porte.
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/RemoteControl/door/1"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        payload = """<?xml version="1.0" encoding="UTF-8"?>
        <RemoteControlDoor xmlns="http://www.isapi.org/ver20/XMLSchema">
            <cmd>close</cmd>
        </RemoteControlDoor>"""

        try:
            resp = requests.put(
                url,
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/xml; charset=UTF-8"},
                auth=auth,
                timeout=Timeout,
            )

            print(f"[{self.name}] HTTP {resp.status_code}")
            print(resp.text)

            if resp.ok:
                print(f"[{self.name}] Porte fermée ✓")
                return True

            return False

        except Exception as e:
            print(f"[{self.name}] Erreur HTTP close: {e}")
            return False


    def door_always_open(self) -> bool:
            """
            Force la porte à rester ouverte en permanence.

            Usage :
            - maintenance
            - accès libre

            """

            url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/RemoteControl/door/1"
            auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

            payload = """<?xml version="1.0" encoding="UTF-8"?>
            <RemoteControlDoor xmlns="http://www.isapi.org/ver20/XMLSchema">
                <cmd>alwaysOpen</cmd>
            </RemoteControlDoor>"""

            try:
                resp = requests.put(
                    url,
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/xml"},
                    auth=auth,
                    timeout=Timeout,
                )

                if resp.ok:
                    print(f"[{self.name}] Porte maintenue OUVERTE ✓")
                    return True

                print(f"[{self.name}] Erreur alwaysOpen: {resp.status_code} — {resp.text}")
                return False

            except Exception as e:
                print(f"[{self.name}] Erreur HTTP alwaysOpen: {e}")
                return False
            

    def door_always_close(self) -> bool:
        """
        Force verrouillage permanent.

        Usage :
        - sécurité
        - lockdown

        ⚠️ override tous les accès RFID
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/RemoteControl/door/1"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        payload = """<?xml version="1.0" encoding="UTF-8"?>
        <RemoteControlDoor xmlns="http://www.isapi.org/ver20/XMLSchema">
            <cmd>alwaysClose</cmd>
        </RemoteControlDoor>"""

        try:
            resp = requests.put(
                url,
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/xml"},
                auth=auth,
                timeout=Timeout,
            )

            if resp.ok:
                print(f"[{self.name}] Porte maintenue FERMÉE ✓")
                return True

            print(f"[{self.name}] Erreur alwaysClose: {resp.status_code} — {resp.text}")
            return False

        except Exception as e:
            print(f"[{self.name}] Erreur HTTP alwaysClose: {e}")
            return False

# ==============================================================================
# ÉTAT PORTE
# ==============================================================================

    def get_door_state(self):
        """
        Retourne uniquement l'état de la porte (True = ouverte, False = fermée)
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/AcsWorkStatus?format=json"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        try:
            resp = requests.get(url, auth=auth, timeout=Timeout)

            if not resp.ok:
                print(f"[{self.name}] Erreur HTTP: {resp.status_code}")
                return None

            data = resp.json().get("AcsWorkStatus", {})
            magnetic = data.get("magneticStatus", [None])[0]

            if magnetic is None:
                print(f"[{self.name}] magneticStatus introuvable")
                return None

            is_open = magnetic == 1

            print(f"[{self.name}] Porte {'OUVERTE' if is_open else 'FERMÉE'}")

            return is_open

        except Exception as e:
            print(f"[{self.name}] Erreur: {e}")
            return None

# ==============================================================================
# CALLBACK / EVENTS
# ==============================================================================

    def setup_listener(self) -> bool:
        """
        Configure le lecteur pour envoyer uniquement les events RFID utiles.

        Events :
        - 1 → accès autorisé
        - 9 → accès refusé

        Étapes :
        1. DELETE config existante
        2. PUT nouvelle config

        ⚠️ si API inaccessible → aucun event reçu
        """

        base_url = f"http://{self.reader_ip}:{self.reader_port}"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        callback_path = Event_Notification_Path
        callback_ip = Uvicorn_Host
        callback_port = Uvicorn_Port

        headers = {
            "Content-Type": "application/xml; charset=UTF-8"
        }

        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
    <HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
    <HttpHostNotification>
    <id>{self.host_id}</id>
    <url>{callback_path}</url>
    <protocolType>HTTP</protocolType>
    <parameterFormatType>JSON</parameterFormatType>
    <addressingFormatType>ipaddress</addressingFormatType>
    <ipAddress>{callback_ip}</ipAddress>
    <portNo>{callback_port}</portNo>
    <httpAuthenticationMethod>none</httpAuthenticationMethod>
    <SubscribeEvent>
    <heartbeat>30</heartbeat>
    <eventMode>list</eventMode>
    <EventList>
    <Event>
    <type>AccessControllerEvent</type>
    <minorAlarm></minorAlarm>
    <minorException></minorException>
    <minorOperation></minorOperation>
    <minorEvent>1,9</minorEvent>
    <pictureURLType>binary</pictureURLType>
    </Event>
    </EventList>
    </SubscribeEvent>
    </HttpHostNotification>
    </HttpHostNotificationList>
    """

        try:
            requests.delete(
                f"{base_url}/ISAPI/Event/notification/httpHosts",
                auth=auth,
                timeout=Timeout,
            )

            put_resp = requests.put(
                f"{base_url}/ISAPI/Event/notification/httpHosts",
                data=payload.encode("utf-8"),
                headers=headers,
                auth=auth,
                timeout=Timeout,
            )

            if put_resp.status_code in (200, 201):
                print(f"[{self.reader_ip}] Listener configuré ✓")
                return True

            print(f"[{self.reader_ip}] Listener refusé ✗")
            return False

        except Exception as e:
            print(f"[{self.reader_ip}] Erreur setup listener: {e}")
            return False

    
    def setup_reader_to_all(self) -> bool:
        """
        Mode debug.

        Configure le lecteur pour envoyer TOUS les événements.

        Permet de découvrir :
        - intercom
        - boutons physiques
        - alarmes
        - événements système

        ⚠️ génère énormément de trafic
        """

        base_url = f"http://{self.reader_ip}:{self.reader_port}"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        callback_path = Event_Notification_Path
        callback_ip = Uvicorn_Host
        callback_port = Uvicorn_Port

        print(f"\n[{self.reader_ip}] Callback ALL : http://{callback_ip}:{callback_port}{callback_path}")

        headers = {
            "Content-Type": "application/xml; charset=UTF-8"
        }

        payload = f"""<?xml version="1.0" encoding="UTF-8"?>
            <HttpHostNotificationList version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
            <HttpHostNotification>
            <id>{self.host_id}</id>
            <url>{callback_path}</url>
            <protocolType>HTTP</protocolType>
            <parameterFormatType>JSON</parameterFormatType>
            <addressingFormatType>ipaddress</addressingFormatType>
            <ipAddress>{callback_ip}</ipAddress>
            <portNo>{callback_port}</portNo>
            <httpAuthenticationMethod>none</httpAuthenticationMethod>
            <SubscribeEvent>
            <heartbeat>30</heartbeat>
            <eventMode>all</eventMode>
            </SubscribeEvent>
            </HttpHostNotification>
            </HttpHostNotificationList>
            """

        try:
            delete_resp = requests.delete(
                f"{base_url}/ISAPI/Event/notification/httpHosts",
                auth=auth,
                timeout=Timeout,
            )

            print(f"DELETE {base_url}/ISAPI/Event/notification/httpHosts -> HTTP {delete_resp.status_code}")
            print(delete_resp.text[:500])

            put_resp = requests.put(
                f"{base_url}/ISAPI/Event/notification/httpHosts",
                data=payload.encode("utf-8"),
                headers=headers,
                auth=auth,
                timeout=Timeout,
            )

            print(f"PUT {base_url}/ISAPI/Event/notification/httpHosts -> HTTP {put_resp.status_code}")
            print(put_resp.text[:500])

            get_resp = requests.get(
                f"{base_url}/ISAPI/Event/notification/httpHosts",
                auth=auth,
                timeout=Timeout,
            )

            print(f"GET {base_url}/ISAPI/Event/notification/httpHosts -> HTTP {get_resp.status_code}")
            print(get_resp.text[:1000])

            return put_resp.status_code in (200, 201)

        except Exception as e:
            print(f"[{self.reader_ip}] Erreur setup_reader_to_all: {e}")
            return False

# ==============================================================================
# RFID / CARTES
# ==============================================================================

    def load_guid(self, guid: str, employee_no: str):
            """
            Ajoute une carte RFID.

            Associe :
            - GUID (badge)
            - employee_no (user)

            ⚠️ aucune création de user possible via API
            """

            url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/CardInfo/SetUp?format=json"
            auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

            payload = {
                "CardInfo": {
                    "employeeNo": str(employee_no),
                    "cardNo": str(guid),
                    "cardType": "normalCard"
                }
            }

            try:
                resp = requests.put(
                    url,
                    json=payload,  # 🔥 important : JSON automatique
                    auth=auth,
                    timeout=Timeout
                )

                if resp.ok:
                    print(f"[{self.name}] GUID {guid} chargé ✓")
                    return True
                else:
                    print(f"[{self.name}] Erreur chargement : {resp.status_code} — {resp.text}")
                    return False

            except Exception as e:
                print(f"[{self.name}] Erreur HTTP : {e}")
            return False


    def delete_guid(self, card_no: str) -> bool:
        """
        Supprime une carte du lecteur.

        ⚠️ suppression globale (pas par utilisateur)
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/CardInfo/Delete?format=json"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        payload = {
            "CardInfoDelCond": {
                "CardNoList": [
                    {
                        "cardNo": str(card_no)
                    }
                ]
            }
        }

        try:
            resp = requests.put(
                url,
                json=payload,
                auth=auth,
                timeout=Timeout,
            )

            if resp.ok:
                print(f"[{self.name}] GUID {card_no} supprimé ✓")
                return True

            print(f"[{self.name}] Erreur suppression GUID {card_no}: HTTP {resp.status_code} — {resp.text}")
            return False

        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] Erreur HTTP suppression GUID {card_no}: {e}")
            return False


    def get_cards(self, limit: int = 100) -> list[dict]:
        """
        Récupère la liste des cartes.

        Paramètre :
        - limit : nombre max retourné

        Retour :
        - liste de dicts cartes

        ⚠️ pagination basique
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/CardInfo/Search?format=json"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        payload = {
            "CardInfoSearchCond": {
                "searchID": "1",
                "searchResultPosition": 0,
                "maxResults": limit
            }
        }

        try:
            resp = requests.post(
                url,
                json=payload,
                auth=auth,
                timeout=Timeout,
            )

            if not resp.ok:
                print(f"[{self.name}] Erreur récupération cartes: HTTP {resp.status_code} — {resp.text}")
                return []

            data = resp.json().get("CardInfoSearch", {})
            cards = data.get("CardInfo", [])

            if isinstance(cards, dict):
                cards = [cards]

            print(f"[{self.name}] {len(cards)} carte(s) récupérée(s)")
            return cards

        except requests.exceptions.RequestException as e:
            print(f"[{self.name}] Erreur HTTP récupération cartes: {e}")
            return []
        
    
    def clear_all_cards(self, batch_size: int = 50, total_deleted: int = 0) -> bool:
        """
        Supprime TOUTES les cartes.

        Fonctionnement :
        - récupère batch
        - supprime batch
        - rappel récursif

        ⚠️ risques :
        - long
        - récursion profonde
        """

        cards = self.get_cards(batch_size)

        if not cards:
            print(f"[{self.name}] CLEAR COMPLET: {total_deleted} cartes supprimées")
            return True

        url_delete = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/CardInfo/Delete?format=json"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        card_nos = [c.get("cardNo") for c in cards if c.get("cardNo")]

        if not card_nos:
            print(f"[{self.name}] Aucune carte valide dans le batch")
            return False

        payload_delete = {
            "CardInfoDelCond": {
                "CardNoList": [{"cardNo": str(card_no)} for card_no in card_nos]
            }
        }

        try:
            resp = requests.put(
                url_delete,
                json=payload_delete,
                auth=auth,
                timeout=Timeout,
            )

            if not resp.ok:
                print(f"[{self.name}] Erreur suppression: {resp.status_code} — {resp.text}")
                return False

            total_deleted += len(card_nos)
            print(f"[{self.name}] Batch supprimé: {len(card_nos)} | Total: {total_deleted}")

            return self.clear_all_cards(batch_size=50, total_deleted=total_deleted)

        except Exception as e:
            print(f"[{self.name}] Erreur HTTP suppression batch: {e}")
            return False

# ==============================================================================
# CONFIG PORTE
# ==============================================================================

    def set_door_open_duration(self, seconds: int) -> bool:
            """
            Définit durée d’ouverture automatique.

            Plage :
            - 1 à 255 secondes

            """

            seconds = int(seconds)

            if seconds < 1 or seconds > 255:
                print(f"[{self.name}] Durée invalide: {seconds}. Valeur attendue: 1-255s")
                return False

            url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/Door/param/1"
            auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

            payload = f"""<?xml version="1.0" encoding="UTF-8"?>
                <DoorParam xmlns="http://www.isapi.org/ver20/XMLSchema" version="2.0">
                    <openDuration>{seconds}</openDuration>
                </DoorParam>"""

            try:
                resp = requests.put(
                    url,
                    data=payload.encode("utf-8"),
                    headers={"Content-Type": "application/xml; charset=UTF-8"},
                    auth=auth,
                    timeout=Timeout,
                )

                if resp.ok:
                    print(f"[{self.name}] Durée ouverture réglée à {seconds}s ✓")
                    return True

                print(f"[{self.name}] Erreur durée: {resp.status_code} — {resp.text}")
                return False

            except Exception as e:
                print(f"[{self.name}] Erreur HTTP durée: {e}")
                return False

# ==============================================================================
# IMAGE
# ==============================================================================

    def take_picture(self, channel_id: int = 101) -> str | None:
            """
            Capture snapshot caméra stockée dans le dossier Picture_Save_Path

            Process :
            - appel HTTP snapshot
            - vérification type
            - sauvegarde disque

            Retour :
            - path fichier
            - None si erreur

            """

            os.makedirs(Picture_Save_Path, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.name}_{self.reader_ip.replace('.', '-')}_{timestamp}.jpg"
            filepath = os.path.join(Picture_Save_Path, filename)

            url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/Streaming/channels/{channel_id}/picture"
            auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

            try:
                resp = requests.get(
                    url,
                    auth=auth,
                    timeout=Timeout,
                )

                if not resp.ok:
                    print(f"[{self.name}] Erreur photo: HTTP {resp.status_code} — {resp.text[:500]}")
                    return None

                content_type = resp.headers.get("Content-Type", "")

                if "image" not in content_type.lower() and not resp.content.startswith(b"\xff\xd8"):
                    print(f"[{self.name}] Réponse non-image: {content_type}")
                    print(resp.text[:500])
                    return None

                with open(filepath, "wb") as f:
                    f.write(resp.content)

                print(f"[{self.name}] Photo sauvegardée: {filepath}")
                return filepath

            except Exception as e:
                print(f"[{self.name}] Erreur HTTP photo: {e}")
                return None

# ==============================================================================
# LUMIÈRE
# ==============================================================================

    def turn_light_on(self, white=50):
        """
        Active LED du lecteur.

        Param :
        - white : intensité (0-100)
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/Image/channels/1/supplementLight"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        xml = f"""
        <SupplementLight>
            <mode>on</mode>
            <brightnessLimit>{white}</brightnessLimit>
        </SupplementLight>
        """

        headers = {"Content-Type": "application/xml"}

        try:
            resp = requests.put(url, data=xml, headers=headers, auth=auth, timeout=Timeout)

            if resp.ok:
                print(f"[{self.name}] Light config updated ✓")
                return True

            print(f"[{self.name}] Error {resp.status_code} - {resp.text}")
            return False

        except Exception as e:
            print(f"[{self.name}] HTTP error: {e}")
            return False


    def turn_light_off(self):
        """
        Désactive LED.
        """


        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/Image/channels/1/supplementLight"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        xml = f"""
        <SupplementLight>
            <mode>off</mode>
            <brightnessLimit>0</brightnessLimit>
        </SupplementLight>
        """

        headers = {"Content-Type": "application/xml"}

        try:
            resp = requests.put(url, data=xml, headers=headers, auth=auth, timeout=Timeout)

            if resp.ok:
                print(f"[{self.name}] Light config updated ✓")
                return True

            print(f"[{self.name}] Error {resp.status_code} - {resp.text}")
            return False

        except Exception as e:
            print(f"[{self.name}] HTTP error: {e}")
            return False
        
# ==============================================================================
# AUDIO
# ==============================================================================
    
    def change_volume_output(self,volume) :
        """
        Change volume haut-parleur.
        """


        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/System/Audio/AudioOut/channels/1"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        xml = f"""
        <AudioOut version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
            <id>1</id>
            <AudioOutVolumelist>
                <AudioOutVlome>
                <type>audioOutput</type>
                <volume>{volume}</volume>
                </AudioOutVlome>
            </AudioOutVolumelist>
            </AudioOut>
        """

        headers = {"Content-Type": "application/xml"}

        try:
            resp = requests.put(url, data=xml, headers=headers, auth=auth, timeout=Timeout)

            if resp.ok:
                print(f"[{self.name}] volume updated ✓")
                return True

            print(f"[{self.name}] Error {resp.status_code} - {resp.text}")
            return False

        except Exception as e:
            print(f"[{self.name}] HTTP error: {e}")
            return False


    def enable_voice_prompt(self, enable: bool):
        """
        Active/désactive voix du lecteur.

        Ex :
        - "Access granted"
        """


        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/AccessControl/AcsCfg?format=json"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

        body = {
            "AcsCfg": {
                "voicePrompt": enable
            }
        }
        return requests.put(url, json=body, auth=auth, timeout=Timeout)

# ==============================================================================
# UTILITAIRE
# ==============================================================================

    def request_get(self,path):
            """
            Wrapper GET brut.

            Usage :
            - debug rapide
            - test endpoint
            """
            url = f"http://{self.reader_ip}:{self.reader_port}{path}"
            auth = HTTPDigestAuth(self.reader_user, self.reader_psw)

            resp = requests.get(url,auth=auth, timeout=Timeout)
            return resp.text

# ==============================================================================
# RÉSEAU / HOTSPOT
# ==============================================================================

    def get_wireless_interfaces(self):
        """
        Retourne configuration réseau du lecteur.
        """


        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/System/Network/interfaces"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)
        return requests.get(url, auth=auth, timeout=Timeout)


    def enable_access_point(self, enabled: bool = True):
        """
        Active/désactive hotspot WiFi.
        """

        url = f"http://{self.reader_ip}:{self.reader_port}/ISAPI/System/Network/interfaces/2/wirelessServer"
        auth = HTTPDigestAuth(self.reader_user, self.reader_psw)
        
        body = """<?xml version="1.0" encoding="UTF-8"?>
            <WirelessServer version="2.0" xmlns="http://www.isapi.org/ver20/XMLSchema">
                <wifiApEnabled>{enabled}</wifiApEnabled>
                <ssid>AP_GS0269846</ssid>
                <WirelessSecurity>
                    <WPA>
                        <algorithmType>AES</algorithmType>
                    </WPA>
                </WirelessSecurity>
            </WirelessServer>""".format(enabled=str(enabled).lower())
        headers = {"Content-Type": "application/xml"}
        return requests.put(url, data=body, headers=headers, auth=auth, timeout=Timeout)
    

