# 🚪 Gateway-ISAPI : Python Wrapper pour HikVision DS-K1T510MBWX-QRE1

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask-lightgrey)](https://flask.palletsprojects.com/)
[![API](https://img.shields.io/badge/Protocol-ISAPI-orange)](https://www.hikvision.com/)

Ce projet est une passerelle (Gateway) conçue pour simplifier l'interaction avec le lecteur biométrique **HikVision DS-K1T510MBWX-QRE1**. L'idée est simple : arrêter de manipuler des requêtes XML ISAPI illisibles et utiliser une interface Python élégante.

## 🎯 Objectif du projet

Faciliter l'accès au lecteur via une classe `Door` qui encapsule toute la logique métier. Cette classe est prête à être importée dans un serveur **Flask**, permettant de piloter le hardware sans se soucier des détails de l'API constructeur.

---

## 🛠 Installation & Setup

Pour démarrer rapidement sans s'embêter avec la configuration manuelle :

```bash
# 1. Cloner le dépôt
git clone https://github.com/Near1807/Gateway-ISAPI.git
cd Gateway-ISAPI

# 2. Installer les dépendances
pip install -r requirements.txt
```

---

## 🏗 La Classe `Door`

La classe `Door` est le cœur de la gateway. Elle représente votre scanner et expose des méthodes simples pour les tâches courantes.

### 📖 Liste des méthodes de la classe `Door`

| Catégorie | Méthode | Description |
| :--- | :--- | :--- |
| **Contrôle Porte** | `open_door()` | Déclenche une ouverture temporaire (selon la durée configurée). |
| | `close_door()` | Force la fermeture immédiate de la porte. |
| | `door_always_open()` | Maintient la porte ouverte en permanence (mode maintenance/libre). |
| | `door_always_close()` | Verrouille la porte en permanence (mode sécurité/lockdown). |
| **État & Diagnostic** | `get_door_state()` | Retourne l'état actuel : `True` (ouverte) ou `False` (fermée). |
| | `request_get(path)` | Wrapper pour effectuer une requête GET brute sur n'importe quel endpoint ISAPI. |
| **Événements (Listener)**| `setup_listener()` | Configure le lecteur pour envoyer les événements RFID (accès autorisé/refusé) au serveur. |
| | `setup_reader_to_all()`| Mode debug : configure le lecteur pour envoyer l'intégralité des événements système. |
| **Gestion RFID** | `load_guid(guid, emp_no)`| Ajoute une carte RFID et l'associe à un numéro d'employé. |
| | `delete_guid(card_no)` | Supprime une carte spécifique du lecteur. |
| | `get_cards(limit)` | Récupère la liste des cartes enregistrées (avec support de pagination). |
| | `clear_all_cards()` | Supprime récursivement TOUTES les cartes du lecteur. |
| **Multimédia & Image** | `take_picture()` | Capture un snapshot depuis la caméra et le sauvegarde localement en `.jpg`. |
| **Audio & Lumière** | `turn_light_on(white)` | Active la LED du lecteur avec une intensité réglable (0-100). |
| | `turn_light_off()` | Désactive la LED du lecteur. |
| | `change_volume_output()`| Règle le volume du haut-parleur du lecteur. |
| | `enable_voice_prompt()` | Active ou désactive les annonces vocales (ex: "Access granted"). |
| **Configuration Système**| `set_door_open_duration()`| Définit le temps (1-255s) pendant lequel la porte reste ouverte après un scan. |
| | `enable_access_point()` | Active ou désactive le point d'accès Wi-Fi (Hotspot) du lecteur. |
| | `get_wireless_interfaces()`| Récupère la configuration détaillée des interfaces réseau du device. |

---

### 💡 Rappel
Toutes ces méthodes utilisent l'authentification **HTTP Digest Auth**. La classe gère automatiquement l'encapsulation des données en **XML** ou **JSON** selon les besoins de l'endpoint ISAPI ciblé.
---

## 📡 Serveur d'Écoute (Event Listener)

Le projet inclut un serveur d'écoute dédié aux notifications :
*   **Traitement en temps réel** : Dès qu'un scan (badge ou visage) est détecté, le serveur reçoit l'info.
*   **Auto-Snapshot** : Le système est configuré pour déclencher une prise de photo à chaque scan réussi, permettant de garder une preuve visuelle de qui entre.

## 💡 Points Clés & Optimisations

*   **Gestion du Digest Auth** : Intégration transparente de l'authentification HikVision.
*   **Zéro XML manuel** : La classe convertit vos commandes Python en requêtes XML conformes au standard ISAPI.
*   **Évitement de latence** : Les appels sont optimisés pour ne pas bloquer les routes de votre API Flask grâce à une fille d'attente.

---
