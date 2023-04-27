# chat/consumers.py
import random
import pafy
import cv2
import asyncio
import json
import base64

from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer

from movie_web_app.actions.movie_detection_manager import DetectMovies


class TrailerStreamingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.scope["session"]["seed"] = random.randint(1, 1000)
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]

        await self.accept()

    async def disconnect(self, close_code):
        pass

    # Receive message from WebSocket
    # Receive message from WebSocket
    async def receive(self, text_data):
        # Get the video URL from the message
        message = json.loads(text_data)

        # Get the video URL from the message
        video_url = message["message"]
        print(video_url)

        # Load the video and seek to the desired frame
        video = pafy.new(video_url)
        stream = video.getbest(preftype="mp4")
        cap = cv2.VideoCapture()
        cap.open(stream.url)


        # Loop through the remaining frames and send them to the client
        while True:
            frame_index = 5  # 0-indexed, so 4 is the 5th frame
            ret = None
            while frame_index > 0:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_index -= 1

            # Read a frame from the video
            ret, frame = cap.read()
            if not ret:
                break

            desired_width = 640
            height, width, _ = frame.shape
            desired_height = int(height * desired_width / width)

            # Resize the frame while maintaining the aspect ratio
            frame = cv2.resize(frame, (desired_width, desired_height))

            # Apply your image processing
            frame = DetectMovies.detect_and_plot(frame, "yolov8n.pt")
            frame = DetectMovies.detect_and_plot(frame, "yolov8_custom.pt")

            # Convert the color space to RGB and encode as JPEG
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()

            # Send the frame to the client
            await self.send(bytes_data=frame_bytes)

            # Sleep for a short time to control the frame rate
            await asyncio.sleep(0.005)

        # Release the video capture when finished
        cap.release()

        # Send a message to the client indicating that the stream has ended
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': 'Stream ended'
        }))

