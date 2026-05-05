"""
================================================================================
Fichier de configuration - Gateway RFID / OPC UA / API
================================================================================

Ce fichier centralise tous les paramètres nécessaires au bon fonctionnement
du système, incluant :

- Connexion au serveur OPC UA (PLC)
- Configuration de l'API FastAPI (Uvicorn)
- Paramètres réseau
- Gestion des timeouts
- Paramètres de performance
- Chemins locaux (certificats, images)

Toutes les valeurs ici doivent être adaptées à l'environnement cible
(développement, test, production).

================================================================================
"""


# ==============================================================================
# OPC UA (Communication avec le PLC / automate industriel)
# ==============================================================================

# URL du serveur OPC UA (PLC)
# Format standard : opc.tcp://<ip>:<port>
# Exemple : automate industriel exposant ses variables via OPC UA
Url_Serveur_PLC = "opc.tcp://192.168.1.10:4840"

# Chemin utilisé pour les notifications d'événements RFID
# Typiquement utilisé dans l'API pour recevoir les événements


# Timeout (en secondes) pour les opérations OPC UA
# Détermine combien de temps on attend une réponse du PLC
Opcua_Timeout = 2


# ==============================================================================
# Sécurité - Certificats client
# ==============================================================================

# Chemin vers le certificat client (authentification OPC UA sécurisée)
# Utilisé si le serveur OPC UA exige TLS / certificats
Client_certificate_path = "path/to/certificate.pem"

# Clé privée associée au certificat
Client_key_path = "path/to/key.pem"


# ==============================================================================
# Configuration serveur FastAPI (Uvicorn)
# ==============================================================================

# Adresse IP sur laquelle le serveur API sera accessible
# Doit être accessible par les équipements externes (lecteurs RFID, etc.)
Uvicorn_Host = "192.168.8.100"

# Port d'écoute du serveur FastAPI
Uvicorn_Port = 8080

# Path de callback des notifications
Event_Notification_Path = "/events/rfid"

# ==============================================================================
# Sécurité et validation des requêtes HTTP
# ==============================================================================

# Taille maximale autorisée pour le body des requêtes HTTP (en bytes)
# Ici : 10 Ko
# Protection contre :
# - attaques par payload volumineux
# - surcharge mémoire
Max_Body_Size = 10 * 1024


# ==============================================================================
# Timeouts réseau
# ==============================================================================

# Timeout pour les requêtes HTTP sortantes (requests)
# Format : (connexion, lecture)
# Exemple :
# - 2 secondes pour établir la connexion
# - 4 secondes pour recevoir la réponse
Timeout = (2, 4)

# ==============================================================================
# Paramètres de fonctionnement interne
# ==============================================================================
# Temps de pause entre cycles courts (boucles rapides)
# Permet d'éviter une surcharge CPU
Sleep_Time = 0.1

# ==============================================================================
# Gestion des fichiers (images RFID, logs visuels, etc.)
# ==============================================================================

# Chemin local où sont stockées les images (ex: captures RFID)
# Attention :
# - Doit exister
# - Permissions d'écriture nécessaires
# - Chemin Windows ici (raw string pour éviter les erreurs d'échappement)
Picture_Save_Path = r"C:\Users\Thomas\Documents\Programmation\Python_Files\Gateway ISAPI\Pictures"