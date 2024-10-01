#!/usr/bin/env python
import cv2
import asyncio
from websockets.asyncio.server import serve, Server, broadcast
from imutils.video import VideoStream
import numpy as np
import requests
import json

import asyncio


from websockets.asyncio.server import  serve

CONNECTIONS = set()
async def register(websocket):
    CONNECTIONS.add(websocket)
    print("Connected")
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)

async def server():
    async with serve(register, "localhost", 8000):
        await asyncio.get_running_loop().create_future()  # run forever

async def video():
    vs = cv2.VideoCapture(1)
    detector = cv2.barcode.BarcodeDetector()

    if not vs.isOpened():
        print("Cannot open camera")
        exit()
        
    succesfull_scans = 0
    failed_scans = 0
    lock = False
    while True:
        if(not lock):
        # vs.open(0)
            ret, frame = vs.read()
            
            if not ret:
                print("Can't receive frame (stream end?). Exiting ...")
                break
            
            # Convert frame to grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            thresholded = gray
            
            detected, corners = detector.detect(thresholded)
            #print(corners)
            if(detected):
                
            # Convert corners to integer values for drawing
                corners = np.array(corners, dtype=np.int32)

                # Draw contours around the corners
                cv2.drawContours(thresholded, corners, -1, (0, 255, 0), 2)
                a = detector.decode(thresholded, corners)
                if a[0]:
                # print(a[0])
                    succesfull_scans += 1
                else: 
                    failed_scans += 1
                
                print(str(succesfull_scans) + " " + str(failed_scans))
                
                if succesfull_scans > 5 and succesfull_scans > failed_scans:
                    failed_scans = 0
                    succesfull_scans = 0
                    r =  requests.get("https://world.openfoodfacts.net/api/v2/product/" + a[0])
                    print(r.status_code)
                    if(r.status_code == 200):
                        print("product found")
                        #broadcast(CONNECTIONS, json.dumps({"command": "scan", "status": "found",  "data": r.json()}))
                    else:
                        print("product not found")
                        #broadcast(CONNECTIONS, json.dumps( {"command": "scan", "status": "not_found", "data": "error"}))
                    print("Barcode detected")
                    print(a[0])
                    
                    await asyncio.sleep(2)
                
                    
                if failed_scans > 10:
                    failed_scans = 0
                    succesfull_scans = 0
                    print("Barcode not detected")
                
            #gray = cv2.cvtColor(gray, cv2.COLOR_BGR2GRAY)
            # Display the resulting gray
            broadcast(CONNECTIONS, gray.tobytes())
            # vs.release()
            await asyncio.sleep(1)

loop = asyncio.get_event_loop()
loop.create_task(server())
loop.create_task(video())
loop.run_forever()

