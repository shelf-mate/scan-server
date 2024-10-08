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


from websockets.asyncio.server import  serve

CONNECTIONS = set()
async def register(websocket):
    CONNECTIONS.add(websocket)
    print("Connected")
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)

async def video():
    vs = cv2.VideoCapture(1)
    detector = cv2.barcode.BarcodeDetector()

    if not vs.isOpened():
        print("Cannot open camera")
        exit()
        
    succesfull_scans = 0
    failed_scans = 0
    while True:
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
                    await asyncio.sleep(10)
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

