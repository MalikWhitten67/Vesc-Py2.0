# app.py
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import threading
import asyncio
import websockets
import json

from vesc import Vesc, is_vesc_parked
from utils import calculate_speed, calculate_throttle_percentage, park_bike,unpark_bike 
from config import MAX_VESC_CURRENT, PIVESC_VERSION, PROFILES
from typedefs import TYPES
connected_clients = set() 

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__, static_folder="UI/dist", static_url_path="/app")
CORS(app)

@app.route('/')
def index():
    return jsonify({"version": PIVESC_VERSION, "message": "Running"})

@app.route('/app/<path:path>')
def static_files(path):
    return send_from_directory(app.static_folder, path)

# WebSocket message handler
async def handle_message(websocket, message):
    try:
        data = json.loads(message) 
        command = data.get("command")
        _data = data.get("data") 

        if command ==  TYPES["COMM_SET_PARKED"]:
            print("Parking bike...")
            parked = park_bike()
            await websocket.send(json.dumps({"parked": parked}))
        elif command == TYPES["COMM_SET_UNPARKED"]:
            unparked = unpark_bike()
            await websocket.send(json.dumps({"unparked": unparked}))
        elif command == TYPES["COMM_GET_PARKED_STATUS"]:
            await websocket.send(json.dumps({"parked": is_vesc_parked()}))
        else:
            await websocket.send(json.dumps({"error": "Unknown command"}))
    except json.JSONDecodeError:
        await websocket.send(json.dumps({"error": "Invalid JSON"}))
    except Exception as e:
        await websocket.send(json.dumps({"error": str(e)}))

# WebSocket connection handler
async def handler(websocket):
    connected_clients.add(websocket)
    try:
        while True:
            vesc_data = Vesc()
            await websocket.send(json.dumps({"event":"vesc_data_recieved", "data": vesc_data}))

            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=1) 
                await handle_message(websocket, message)
            except asyncio.TimeoutError:
                continue
    except websockets.exceptions.ConnectionClosed:
        print("Client disconnected")
    finally:
        connected_clients.remove(websocket)
        print("Client removed")

# Threaded Flask runner
def run_flask():
    app.run(host='0.0.0.0', port=5000, debug=False)

# Async main to run both servers
async def main():
    print("Starting WebSocket server...")
    ws_server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("WebSocket server running on ws://0.0.0.0:8765")

    # Start Flask in a separate thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()

    await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())
