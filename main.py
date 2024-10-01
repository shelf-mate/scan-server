#!/usr/bin/env python
import cv2
import asyncio
from websockets.asyncio.server import serve, Server, broadcast
from imutils.video import VideoStream

import asyncio


from websockets.asyncio.server import broadcast, serve

CONNECTIONS = set()

async def register(websocket):
    CONNECTIONS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)


async def server():
    async with serve(register, "localhost", 8000):
        await asyncio.get_running_loop().create_future()  # run forever

async def video():
    vs = cv2.VideoCapture(0)
    if not vs.isOpened():
        print("Cannot open camera")
        exit()
    while True:
        ret, frame = vs.read()
        if not ret:
            print("Can't receive frame (stream end?). Exiting ...")
            break
        #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Display the resulting frame
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) == ord('q'):
            break

async def main():
    await asyncio.gather(
        video()
    )



asyncio.run(main())
