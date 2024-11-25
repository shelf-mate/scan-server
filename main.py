#!/usr/bin/env python
import cv2
import asyncio
from websockets.asyncio.server import serve, Server, broadcast
import numpy as np
import requests
import json

import asyncio
from picamera2 import Picamera2
from dotenv import load_dotenv
from libcamera import controls
import os
from gpiozero import PWMOutputDevice
from time import sleep

load_dotenv()  # take environment variables from .env.

BUZZER_PIN = 12



def play_buzzer_tone(frequency, duration):
    """
    Plays a tone at a specific frequency for a given duration using PWMOutputDevice.

    Args:
        pin (int): The GPIO pin number where the buzzer is connected.
        frequency (float): The frequency of the tone in Hz.
        duration (float): The duration of the tone in seconds.
    """
    # Initialize the PWMOutputDevice for the buzzer
    buzzer = PWMOutputDevice(BUZZER_PIN)

    # Set the frequency and duty cycle
    buzzer.frequency = frequency
    buzzer.value = 0.55  # 50% duty cycle for a clear tone

    # Play the tone for the specified duration
    sleep(duration)

    # Stop the tone
    buzzer.off()

    # Clean up by stopping the buzzer
    buzzer.close()


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
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration(main={"format": 'XRGB8888', "size": (1920, 1080)}))
    picam2.start()
    picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 25})
    detector = cv2.barcode.BarcodeDetector()

    succesfull_scans = 0
    failed_scans = 0
    while True:
        if not block_scan:
            frame = picam2.capture_array()
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
                    play_buzzer_tone(2300, 0.25)
                    failed_scans = 0
                    succesfull_scans = 0
                    broadcast(CONNECTIONS, json.dumps({"command": "scan", "data": {"ean": ean}}))
                    await asyncio.sleep(1)
                if failed_scans > 10:
                    broadcast(CONNECTIONS, json.dumps({"command": "error", "data": { "message": "Error accessing camera!"}}))
                    print("Failed to scan")
                    failed_scans = 0
                    succesfull_scans = 0
        await asyncio.sleep(0.001)

async def main():
    server = await serve(register, "0.0.0.0", os.getenv("PORT"))
    
    asyncio.create_task(video())
    
    await server.wait_closed()

asyncio.run(main())

