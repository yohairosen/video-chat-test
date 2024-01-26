from flask import Flask, request, jsonify
import base64
import time
import json
import asyncio
import os
import re
import numpy as np
import shutil
from flask_sock import Sock
from tools import audio_pre_process, video_pre_process, generate_video, audio_process
import edge_tts

app = Flask(__name__)
sock = Sock(app)

video_list = []

async def main(voicename: str, text: str, OUTPUT_FILE):
    communicate = edge_tts.Communicate(text, voicename)
    with open(OUTPUT_FILE, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                pass

def send_information(path, ws):

        print('传输信息开始！')
        #path = video_list[0]
        ''''''
        with open(path, 'rb') as f:
            video_data = base64.b64encode(f.read()).decode()

        data = {
                'video': 'data:video/mp4;base64,%s' % video_data,
                }
        json_data = json.dumps(data)

        ws.send(json_data)

def txt_to_audio(text_):
    audio_list = []
    # audio_path = 'data/audio/aud_0.wav'
    audio_path = 'data/audio/silent.wav'
    # voicename = "zh-CN-YunxiaNeural"
    voicename = "en-AU-WilliamNeural"
    text = text_
    asyncio.run(main(voicename, text, audio_path))
    audio_process(audio_path)

@sock.route('/dighuman')
def echo_socket(ws):
    print('Connection established!')
    while True:
        message = ws.receive()
        if len(message) == 0:
            return 'Input message is empty'
        else:
            txt_to_audio(message)
            audio_path = 'data/audio/aud_0.wav'
            audio_path_eo = 'data/audio/aud_0_eo.npy'
            video_path = 'data/video/results/ngp_0.mp4'
            output_path = 'data/video/results/output_0.mp4'
            generate_video(audio_path, audio_path_eo, video_path, output_path)
            video_list.append(output_path)
            send_information(output_path, ws)

def run_app():
    audio_pre_process()
    video_pre_process()
    app.run("0.0.0.0", port=5000, use_reloader=False)

if __name__ == '__main__':
    run_app()
