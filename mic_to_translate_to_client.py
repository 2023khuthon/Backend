import websockets
import pyaudio
import asyncio
import json
import logging
import time
from io import DEFAULT_BUFFER_SIZE
from requests import Session
import requests

import const
import language_translation_papago

API_BASE = "https://openapi.vito.ai"

url = "http://172.21.119.171:8888/text"

class RTZROpenAPIClient:
    def __init__(self, client_id, client_secret):
        self._logger = logging.getLogger(__name__)
        self.client_id = client_id
        self.client_secret = client_secret
        self._sess = Session()
        self._token = None

    @property
    def token(self):
        if self._token is None or self._token["expire_at"] < time.time():
            resp = self._sess.post(
                API_BASE + "/v1/authenticate",
                data={"client_id": self.client_id, "client_secret": self.client_secret},
            )
            resp.raise_for_status()
            self._token = resp.json()
        return self._token["access_token"]

    async def streaming_transcribe(self, config=None):
        if config is None:
            config = dict(
                sample_rate="44100",
                encoding="LINEAR16",
                use_itn="true",
                use_disfluency_filter="true",
                use_profanity_filter="false",
                use_paragraph_splitter="true"
            )
        STREAMING_ENDPOINT = "wss://{}/v1/transcribe:streaming?{}".format(
            API_BASE.split("://")[1], "&".join(map("=".join, config.items()))
        )
        conn_kwargs = dict(extra_headers={"Authorization": f"bearer {self.token}"})

        async def streamer(websocket):
            p = pyaudio.PyAudio()

            # 오디오 스트림 열기
            stream = p.open(format=pyaudio.paInt16,
                            channels=1,
                            rate=44100,
                            input=True,
                            frames_per_buffer=DEFAULT_BUFFER_SIZE)

            print("Streaming started.")

            while True:
                # 마이크에서 데이터 읽기
                data = stream.read(DEFAULT_BUFFER_SIZE)
                await websocket.send(data)
            # 스트림 닫기
            stream.stop_stream()
            stream.close()
            p.terminate()
            await websocket.send("EOS")

        async def transcriber(websocket):
            async for msg in websocket:
                msg = json.loads(msg)
                print(msg)
                if msg["final"]:
                    print("final ended with " + msg["alternatives"][0]["text"])
                    translated_text = language_translation_papago.translate_text(msg["alternatives"][0]["text"], 'en')
                    if translated_text.strip() != "":
                        requests.post(url, data=translated_text)

        async with websockets.connect(STREAMING_ENDPOINT, **conn_kwargs) as websocket:
            await asyncio.gather(
                streamer(websocket),
                transcriber(websocket),
            )


if __name__ == "__main__":
    CLIENT_ID = const.returnzero_id
    CLIENT_SECRET = const.returnzero_secret
    client = RTZROpenAPIClient(CLIENT_ID, CLIENT_SECRET)
    asyncio.run(client.streaming_transcribe())
