# Accès à distance (façon Veyon Master)
- `server.py` + `index.html` : relais et visualiseur web, à héberger sur Render.
- `agent.py` : à lancer sur le PC à contrôler (`pip install -r agent-requirements.txt`, puis `python agent.py https://VOTRE-SERVICE.onrender.com`).
L'agent demande l'autorisation, affiche une bannière rouge et un bouton Arrêter. À n'utiliser que sur des PC dont vous êtes responsable, avec l'accord de leurs utilisateurs.
