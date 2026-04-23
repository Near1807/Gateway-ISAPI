from classes import Door

Url_Serveur_PLC = "opc.tcp://192.168.1.10:4840"
URL_Event_Notification = "/events/rfid"

Client_certificate_path = "path/to/certificate.pem"
Client_key_path = "path/to/key.pem"

Uvicorn_Host = "0.0.0.0"
Uvicorn_Port = 8080
Redis_url = "redis://localhost:6379"

Check_State_Time = 30
Sleep_Time = 0.1
Reconnect_Time_PLC = 1

DOORS = {
    "127.0.0.1": Door(
        name="Door_1",
        reader_ip="127.0.0.1",
        reader_user="admin",
        reader_psw="admin",
        door_state_output_id=1,
        guid_node_id="ns=1;s=Guid_Tag",
        door_node_id="ns=2;s=Door_Tag",
        door_state_node_id="ns=3;s=Door_State_Tag",
        guid_flag_node_id="ns=1;s=Guid_Flag_Tag",
        door_state_flag_node_id="ns=3;s=Door_State_Flag_Tag"
    ),
    # "192.168.1.21": Door(name="Door_2", ...)
}