# Définition du projet

## Sujet : Création d’un système de serrure connectée et sécurisée

L’objectif de ce projet est de concevoir une serrure intelligente contrôlée à distance et gérée par un système web centralisé.

### Côté web :

L’administrateur dispose d’une interface connectée à une base de données SQL. Celle-ci lui permet de :

- Visualiser la liste de tous les détenteurs de carte RFID, leur rôle (niveau d’accès) et les logs d’utilisation (date et heure de la dernière utilisation).

- Consulter la liste des serrures installées dans l’établissement, pouvoir en ajouter, avec leur identifiant unique (ID) et les rôles autorisés à les déverrouiller.

- Créer, modifier ou supprimer des rôles et utilisateurs, puis leur attribuer les droits d’accès appropriés.

Ce système vise à centraliser la gestion des accès et à renforcer la sécurité de l’établissement.

Le serveur web sera hébergé en ligne sur un broker MQTT public, où il agira en tant que client MQTT.
Il pourra ainsi surveiller les échanges sur le broker, identifier les cartes RFID détectées et mettre à jour la base de données en temps réel.


## Composants utilisés :

- ESP32

- Lecteur RFID

- Servomoteur

- Badge RFID

- Écran LCD I2C

- Breadboards (x2)

## Fonctionnement et rôle des composants

- ESP32 : Sert de microcontrôleur principal. Il gère la communication entre le lecteur RFID, la base de données (via le réseau Wi-Fi), le servomoteur et l’écran LCD.

- Lecteur RFID : Permet d’identifier la carte présentée. Il transmet l’ID au microcontrôleur, qui vérifie si l’utilisateur dispose des droits d’accès pour déverrouiller la serrure.

- Servomoteur : Simule le mécanisme d’ouverture ou de fermeture de la serrure selon l’autorisation accordée.

- Badge RFID : Représente la carte d’accès de l’utilisateur.

- Écran LCD I2C : Affiche en temps réel l’état de la serrure (verrouillée ou déverrouillée).

- Breadboards : Permettent d’assurer les connexions électriques entre les différents composants du montage.

# Convention de nommage

*PascalCase* : nom de fonctions et fichiers, *camelcase* pour les variables


# Structure du projet 

```
IOT/
│
├─ main.py                  # Point d'entrée, inclut tout : routes, WebSocket, MQTT
├─ db.py                    # Initialisation de la base de données (init_db)
├─ mqtt_handler.py          # Connexion et gestion MQTT
├─ utils.py                 # Fonctions utilitaires, ex : connections WebSocket, notify_clients
│
├─ routes/                  # Routes séparées par type d'objet, si tu veux organiser (optionnel)
│  ├─ cartes.py             # Routes /cartes/... (ajout, suppression, modification)
│  ├─ serrures.py           # Routes /serrures/...
│  ├─ roles.py              # Routes /roles/...
│  ├─ logs.py               # Routes /logs/...
│  └─ __init__.py           # Pour que le dossier soit un package Python
│
├─ templates/
│  └─ index.html            # Page unique qui affiche tout : cartes, serrures, rôles, logs
│
├─ static/
│  ├─ styles.css            # Styles CSS
│  └─ script.js             # JS de la page (WebSocket, fetch, refresh)
│
└─ serrure.db               # Base de données SQLite

```

_LEFEBBVRE Lou, CABANES Hugo, CAETANO Maël_