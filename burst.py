import requests

for i in range(10):
    print(f"Request {i+1}")
    url = "http://localhost:8080/events/rfid"
    data = f"""<?xml version="1.0" encoding="UTF-8"?>
        <EventNotificationAlert>
            <AccessControllerEvent>
                <cardNo>123456789</cardNo>
                <requestNo>{i}</requestNo>
            </AccessControllerEvent>
        </EventNotificationAlert>"""
    try:
        response = requests.post(url, data=data.encode("utf-8"),
                                 headers={"Content-Type": 'application/xml; charset="UTF-8"'})
        print("Response:", response.status_code, response.text)
    except Exception as e:
        print("Error:", e)