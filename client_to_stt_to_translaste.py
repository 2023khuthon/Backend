import websockets
import asyncio
import json
import logging
import time
import io
from requests import Session
import speech_recognition as sr
import requests

import const
import language_translation_papago

API_BASE = "https://openapi.vito.ai"
url = "http://172.21.119.171:8888/text"

class RTZROpenAPIClient:
    def __init__(self, client_id, client_secret, web_client_websocket):
        self._logger = logging.getLogger(__name__)
        self.client_id = client_id
        self.client_secret = client_secret
        self._sess = Session()
        self._token = None
        self.web_client_websocket = web_client_websocket

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

        async def streamer(zero_websocket, web_websocket):

            print("Streaming started.")

            while True:
                try:
                    blob_data = await web_websocket.recv()

                    blob_stream = io.BytesIO(blob_data)

                    audio_data = sr.AudioData(blob_stream.read(), sample_rate=44100, sample_width=2)
                    binary_data = audio_data.get_raw_data()
                    print(repr(binary_data[:20]))
                    # int16_array = struct.unpack("<" + "h" * (len(binary_data) // 2), binary_data)
                    # print(int16_array[:5])
                    # # print(len(int16_array))
                    await zero_websocket.send(audio_data.get_raw_data())
                except websockets.exceptions.ConnectionClosed:
                    break

            await zero_websocket.send("EOS")

        async def transcriber(zero_websocket, web_websocket):
            async for msg in zero_websocket:
                msg = json.loads(msg)
                print(msg)
                if msg["final"]:
                    print("final ended with " + msg["alternatives"][0]["text"])
                    translated_text = language_translation_papago.translate_text(msg["alternatives"][0]["text"], 'en')
                    print(translated_text)
                    try:
                        await web_websocket.send(translated_text)
                    except websockets.exceptions.WebSocketException:
                        break

        async with websockets.connect(STREAMING_ENDPOINT, **conn_kwargs) as websocket:
            await asyncio.gather(
                streamer(websocket, self.web_client_websocket),
                transcriber(websocket, self.web_client_websocket),
            )


async def process_audio(websocket, path):
    print("Client Connected")

    client = RTZROpenAPIClient(const.returnzero_id, const.returnzero_secret, websocket)
    await client.streaming_transcribe()

if __name__ == "__main__":
    start_server = websockets.serve(process_audio, "172.21.119.171", 8766)

    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()
