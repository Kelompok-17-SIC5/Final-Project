from flask import Flask, jsonify, request
import paho.mqtt.client as mqtt
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from requests import Request
import pymongo


###########################################################################################################################################################################
#                                  Connection
uri = "mongodb+srv://Farhan:Farhan26@cluster0.r6zjxko.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
db = client['SIC'] # ganti sesuai dengan nama database kalian
my_collections = db['Sensor']

def dbConnect():
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
        






app = Flask(__name__)

MQTT_BROKER = "test.mosquitto.org"
MQTT_PORT = 1883
MQTT_KEEPALIVE_INTERVAL = 10000
TOPIC_TEMPERATURE = "/sensor/data/temperature"
TOPIC_HUMIDITY = "/sensor/data/humidity"
TOPIC_AIR_QUALITY = "/sensor/data/air_quality"
TOPIC_SMOKE = "/sensor/data/smoke_value"

temperature = None
humidity = None
airQuality = None
SmokeValue = None
data = None


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT Broker with result code {rc}")
    client.subscribe(TOPIC_TEMPERATURE)
    client.subscribe(TOPIC_HUMIDITY)
    client.subscribe(TOPIC_AIR_QUALITY)
    client.subscribe(TOPIC_SMOKE)
    

# Membuat fungsi yang men-decode pesan dari mqtt
def on_message(client, userdata, msg):
    global temperature, humidity, airQuality, SmokeValue, data
    if msg.topic == TOPIC_TEMPERATURE:
        temperature = float(msg.payload.decode())
    elif msg.topic == TOPIC_HUMIDITY:
        humidity = float(msg.payload.decode())
    elif msg.topic == TOPIC_AIR_QUALITY:
        airQuality = float(msg.payload.decode())
    elif msg.topic == TOPIC_SMOKE:
        SmokeValue = float(msg.payload.decode())
        if SmokeValue <= 300:
            SmokeValue = "No Smoke"
        elif SmokeValue <= 500:
            SmokeValue = "Low Smoke"
        else:
            SmokeValue = "High Smoke"
    data = {
        "Temperature" : temperature,
        "Humidity": humidity,
        "AQI": airQuality,
        "Smoke Level": SmokeValue
    }
    
    if (data["Temperature"] != None) and (data["Humidity"] != None) and (data["AQI"] != None) and (data["Smoke Level"] != None) :
        print("Data : ", data)
    else:
        pass
    
    # results = my_collections.insert_one(data)
    # print(results.inserted_id)

# Menginisialisasikan mqtt client
mqtt_client = mqtt.Client()
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEPALIVE_INTERVAL)
mqtt_client.loop_start()


#Membuat route untuk halaman default
@app.route('/')
def index():
    dbConnect()
    return "MQTT to HTTP API Server"

#Membuat route untuk data temperatur dan menginisialisasikan dengan method get pada API
@app.route('/Home/Temperature', methods=['GET', 'POST'])
def temperature():
    global data
    if request.method == 'GET':
        if data is not None:
            return jsonify({"Data": data})
        else:
            return jsonify({"error": "No temperature data available"}), 404
    if request.method == 'POST':
        if request.is_json:
            req = request.get_json()
            data = req['Data']
            # result = my_collections.insert_one({"temperature": temperature})
            # print(temperature)
            # return jsonify({"temperature": int(temperature),"inserted_id": str(result.inserted_id)}), 200
            return jsonify({"Data" : {
                "Temperature" : data["Temperature"],
                "Humidity": data["Humidity"],
                "AQI": data["AQI"],
                "Smoke Level": data[ "Smoke Level"]
            }})
        else:
            return jsonify({"error": "Request content type must be application/json"}), 400
    
    
    


#Menjalankan API dengan port 8000
if __name__ == '__main__':
    app.run(host='0.0.0.0',port=8000)
