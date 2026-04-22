from flask import *
from library import *
import threading
import json
import xmltodict

app = Flask(__name__)

@app.route("/",methods=["POST"])
def Home():
    return "Hello World !"

@app.route(URL_Event_Notification,methods=["POST"])
def Notifications():
    data = request.data
    json = xmltodict.parse(data)
    card_no = json["EventNotificationAlert"]["AccessControllerEvent"]["cardNo"]
    #NewGuidConnexion(card_no)
    return(card_no)
    


if __name__ == "__main__":
    threading.Thread(target=PLC_Polling, args=(url_Serveur_PLC,), daemon=True).start()

    app.run(host=Flask_Host,port=Flask_Port)