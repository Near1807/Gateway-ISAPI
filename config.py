Url_Serveur_PLC= "opc.tcp://192.168.1.10:4840"
URL_Event_Notification= "/events/rfid"

Client_certificate_path = "path/to/certificate.pem"
Client_key_path = "path/to/key.pem"

Guid_NodeId = "ns=1;s=Guid_Tag"
Door_NodeId = "ns=2;s=Door_Tag"
Door_State_NodeId = "ns=3;s=Door_State_Tag"
Flag_NodeId = "ns=3;s=Flag_Node_Tag" #repasse à 0 apres x temps 
#Node Id Reader + infos complémentaire + ip + ...
#Etat scanner check si il est toujours vivant
#Recherches retours Infos Etat général scanner 

Reader_IP = "0.0.0.0"
Reader_User = "admin"
Reader_Psw = "admin"
Door_State_Output_id = 1

Uvicorn_Host = "0.0.0.0"
Uvicorn_Port = 8080
Redis_url = "redis://localhost:6379"
Guid_Request_Queue = "Guid_Queue"





check_state_time = 30
sleep_time = 0.1