import random
import pafy
import cv2
import asyncio
import json

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
        data = json.loads(text_data)

        video_url = data["youtube_url"]
        print(video_url)

        video = pafy.new(video_url)
        stream = video.getbest(preftype="mp4")
        cap = cv2.VideoCapture()
        cap.open(stream.url)

        while True:
            frame_index = 5
            ret = None
            while frame_index > 0:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_index -= 1

            ret, frame = cap.read()
            if not ret:
                break

            desired_width = 640
            height, width, _ = frame.shape
            desired_height = int(height * desired_width / width)

            frame = cv2.resize(frame, (desired_width, desired_height))

            frame = DetectMovies.process_frame(frame, data['yolo'], data['categories'], data['conf'])

            ret, jpeg = cv2.imencode('.jpg', frame)
            frame_bytes = jpeg.tobytes()

            await self.send(bytes_data=frame_bytes)
            await asyncio.sleep(0.005)

        cap.release()

        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': 'Stream ended'
        }))
