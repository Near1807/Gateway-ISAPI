# Gateway-ISAPI : Interface Python pour HikVision DS-K1T510MBWX-QRE1

Ce projet est une passerelle (Gateway) conçue pour simplifier radicalement l'interaction avec le lecteur biométrique et de contrôle d'accès **HikVision DS-K1T510MBWX-QRE1**. 

L'objectif est d'abstraire la complexité de l'API ISAPI propriétaire en fournissant une interface Python intuitive via une classe `Door`. Plus besoin de manipuler des requêtes XML/HTTP complexes : vous gérez votre scanner comme un objet Python, parfaitement adapté pour un serveur **Flask** sans les prises de tête habituelles de l'API.

## 🚀 Fonctionnalités principales

- **Abstraction `Door`** : Une classe unique pour piloter le scanner, la gâche et la caméra.
- **Serveur d'écoute (Listener)** : Setup d'un serveur pour traiter les notifications (events) en temps réel.
- **Capture Multimédia** : Gestion de la prise de photos automatique durant les scans pour archivage.
- **Intégration Flask** : Structure légère conçue pour être appelée par des routes API.

## 🛠 Installation

Pour utiliser ce projet, clonez le dépôt et installez les dépendances nécessaires :

```bash
# 1. Cloner le projet
git clone [https://github.com/Near1807/Gateway-ISAPI.git](https://github.com/Near1807/Gateway-ISAPI.git)
cd Gateway-ISAPI

# 2. Installer les dépendances
pip install -r requirements.txt
````
