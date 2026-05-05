"""
================================================================================
Module : Gestion des événements RFID + interaction lecteurs + parsing
================================================================================

Ce module contient toute la logique métier liée à :

- La détection et interprétation des événements RFID
- La configuration des lecteurs (Hikvision ou équivalent)
- Le mapping des portes physiques vers des objets logiciels
- Le traitement des événements entrants
- L'extraction des données depuis des payloads HTTP (multipart)

Il agit comme couche intermédiaire entre :
- L'API (FastAPI)
- Les équipements physiques (lecteurs / portes)
- Le système OPC UA (via Door)

================================================================================
"""

# ==============================================================================
# Imports
# ==============================================================================

import xmltodict                  # Parsing XML (potentiellement utilisé ailleurs)
from config import *              # Variables globales de configuration
from time import sleep            # Gestion des pauses (non utilisé ici directement)
from opcua.ua.uaerrors import UaStatusCodeError  # Gestion erreurs OPC UA
from opcua import Client          # Client OPC UA
import json                       # Parsing JSON
from doors import *               # Classe Door et logique associée


# ==============================================================================
# Détection d'ouverture locale (reader autonome)
# ==============================================================================

def Local_Opening(event: dict) -> bool:
    """
    Détermine si une ouverture de porte a été effectuée localement
    par le lecteur (décision prise depuis sa mémoire locale).

    Contexte :
    - Certains lecteurs RFID peuvent prendre des décisions localement
      (mode offline ou cache)
    - Cette fonction permet de détecter ce cas

    Paramètres :
    - event (dict) : événement brut provenant du lecteur

    Retour :
    - True  → accès accordé localement
    - False → autre type d'événement

    IMPORTANT :
    - La valeur `subEventType` doit être adaptée selon le matériel réel
    - Ici : 1 = accès autorisé (hypothèse actuelle)

    Exemple d'évolution :
    - Ajouter plusieurs codes autorisés
    - Mapper dynamiquement selon fabricant
    """

    sub_event = event.get("subEventType")

    access_granted = 1  # Code supposé pour "accès autorisé"

    if sub_event == access_granted:
        return True
    else:
        return False


# ==============================================================================
# Initialisation des portes
# ==============================================================================

def door_set_up():
    """
    Initialise et configure toutes les portes du système.

    Rôle :
    - Créer les objets Door
    - Associer chaque porte à son IP
    - Définir les paramètres OPC UA et réseau

    Structure retournée :
    - dict { ip: Door }

    Paramètres configurés :
    - Identification lecteur
    - Connexion HTTP (IP, port, credentials)
    - Mapping OPC UA (node IDs)
    - Flags de synchronisation

    IMPORTANT :
    - Chaque IP doit être unique
    - Les Node IDs OPC UA doivent correspondre au PLC réel
    - Les credentials doivent être sécurisés en production

    Évolution possible :
    - Charger depuis fichier JSON / DB
    - Support multi-portes dynamique
    """

    DOORS = {
        "192.168.8.1": Door(
            reader_id=1,
            name="Door_1",
            reader_ip="192.168.8.1",
            reader_port=80,
            reader_user="admin",
            reader_psw="Automatec",

            # Sortie physique liée à l'état de la porte
            door_state_output_id=1,

            # ================= OPC UA Nodes =================
            guid_node_id="ns=1;s=Guid_Tag",
            door_node_id="ns=2;s=Door_Tag",
            door_state_node_id="ns=3;s=Door_State_Tag",

            # Flags
            guid_flag_node_id="ns=1;s=Guid_Flag_Tag",
            door_state_flag_node_id="ns=3;s=Door_State_Flag_Tag"
        )
    }

    return DOORS


# ==============================================================================
# Configuration des lecteurs (callback HTTP)
# ==============================================================================

def configure_readers(doors):
    """
    Configure chaque lecteur pour qu'il envoie ses événements
    vers le serveur API (callback).

    Rôle :
    - Appeler `setup_listener()` sur chaque Door
    - Pousser l'URL de callback vers le lecteur

    Paramètres :
    - doors (dict) : mapping IP → Door

    Gestion erreurs :
    - Log succès / échec
    - Catch exceptions réseau ou API

    IMPORTANT :
    - Le lecteur doit être accessible sur le réseau
    - L'API doit être joignable depuis le lecteur

    Effet :
    - Les lecteurs envoient ensuite leurs événements automatiquement
    """

    for ip, door in doors.items():
        try:
            ok = door.setup_listener()

            if ok:
                print(f"[{ip}] Setup listener : OK")
            else:
                print(f"[{ip}] Setup listener : FAILED")

        except Exception as e:
            print(f"[{ip}] Setup listener : ERROR -> {e}")


# ==============================================================================
# Traitement des événements
# ==============================================================================

def process_event(data: dict, doors: dict):
    """
    Traite un événement reçu depuis un lecteur RFID.

    Étapes :
    1. Filtrage des heartbeats
    2. Extraction des informations utiles
    3. Identification de la porte concernée
    4. Logging de l'événement
    5. Action métier (ex: prise de photo)

    Paramètres :
    - data (dict) : événement brut parsé
    - doors (dict) : mapping IP → Door

    Mapping des événements :
    - 1  → accès autorisé
    - 9  → accès refusé
    - 21 → porte ouverte
    - 22 → porte fermée

    IMPORTANT :
    - Les codes `subEventType` dépendent du fabricant
    - À ajuster selon la documentation du lecteur

    Effets possibles :
    - Logging console
    - Interaction avec la porte
    - Capture d'image

    Améliorations possibles :
    - Ajout de logs structurés (JSON)
    - Intégration avec base de données
    - Envoi vers système externe (MQTT, Kafka, etc.)
    """

    EVENT_MAP = {
        1: "✅ accès OK",
        9: "❌ accès refusé",
        21: "🚪 porte ouverte",
        22: "🔒 porte fermée",
    }

    # Filtrage des messages heartbeat (bruit réseau)
    if data.get("eventType") == "heartBeat":
        print("💤 heartbeat")
        return

    # Extraction des infos principales
    event = data.get("AccessControllerEvent", {})
    sub = event.get("subEventType")
    ip = data.get("ipAddress")

    # Recherche de la porte associée
    door = doors.get(ip)

    if door:
        print(f"[{door.name}] {EVENT_MAP.get(sub, f'❓ inconnu ({sub})')}")

        # Action métier : prise de photo
        # (probablement pour audit ou sécurité)
        door.take_picture(101)

    else:
        # Cas où l'IP n'est pas connue
        print(f"[{ip}] {EVENT_MAP.get(sub, f'❓ inconnu ({sub})')}")


# ==============================================================================
# Extraction des événements depuis payload HTTP
# ==============================================================================

def extract_event(body: bytes) -> dict | None:
    """
    Extrait un objet JSON depuis un body HTTP brut.

    Contexte :
    - Les lecteurs envoient souvent du multipart/form-data
    - Le JSON est "embedded" dans le payload
    - On doit donc extraire manuellement

    Méthode :
    - Recherche du premier '{'
    - Recherche du dernier '}'
    - Extraction du segment JSON
    - Parsing via json.loads

    Paramètres :
    - body (bytes) : corps brut de la requête HTTP

    Retour :
    - dict → événement parsé
    - None → si parsing impossible

    Limites :
    - Méthode fragile si plusieurs JSON présents
    - Dépend du format exact du constructeur

    Améliorations possibles :
    - Utiliser un vrai parser multipart
    - Valider le schéma JSON
    """

    start = body.find(b"{")
    end = body.rfind(b"}")

    # Vérification validité extraction
    if start == -1 or end == -1 or end <= start:
        return None

    try:
        return json.loads(
            body[start:end + 1].decode("utf-8", errors="ignore")
        )
    except Exception as e:
        print(f"Erreur parsing event: {e}")
        return None