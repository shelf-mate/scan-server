#!/usr/bin/env python
import cv2
import asyncio
from websockets.asyncio.server import serve, Server, broadcast
from imutils.video import VideoStream
import numpy as np
import requests
import json

import asyncio

from dotenv import load_dotenv

import os

load_dotenv()  # take environment variables from .env.


block_scan = False

from websockets.asyncio.server import  serve

CONNECTIONS = set()
async def handle_message(raw_data):
    data = json.loads(raw_data)
    global block_scan
    if data["command"] == "block":
        print("Blocking scan: " + str(data["data"]))
        block_scan = data["data"]


async def register(websocket):
    global block_scan
    CONNECTIONS.add(websocket)
    print("Connection opened")
    try:
        while True:
            data = await websocket.recv()
            await handle_message(data)
    finally:
        print("finally")
        CONNECTIONS.remove(websocket)

async def video():
    global block_scan
    vs = cv2.VideoCapture(1)
    detector = cv2.barcode.BarcodeDetector()

    if not vs.isOpened():
        print("Cannot open camera")
        exit()
        
    succesfull_scans = 0
    failed_scans = 0
    while True:
        if not block_scan:
            ret, frame = vs.read()
            if not ret:
                broadcast(CONNECTIONS, json.dumps({"command": "error", "data": { "message": "Error accessing camera"}}))
                print("Can't receive frame (stream end?). Exiting ...")
                break
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)            
            detected, corners = detector.detect(gray)
            if(detected):
                cv2.imwrite("barcode.png", gray)
                decoded = detector.decode(gray, corners)
                ean = decoded[0]
                if ean:
                    succesfull_scans += 1
                else: 
                    failed_scans += 1                
                if succesfull_scans > 5 and succesfull_scans > failed_scans:
                    print("Scanned: " + ean)
                    failed_scans = 0
                    succesfull_scans = 0
                    broadcast(CONNECTIONS, json.dumps({"command": "scan", "data": {"ean": ean}}))
                    await asyncio.sleep(1)
                if failed_scans > 10:
                    print("Failed to scan")
                    failed_scans = 0
                    succesfull_scans = 0
        await asyncio.sleep(0.001)

async def main():
    server = await serve(register, "0.0.0.0", os.getenv("PORT"))
    
    asyncio.create_task(video())
    
    await server.wait_closed()

asyncio.run(main())

