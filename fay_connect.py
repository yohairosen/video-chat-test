"""
郭泽斌于2023.04.29参照app.py创建，用于连接github开源项目 Fay 数字人
"""

import base64
import time
import json
import gevent
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from tools import audio_pre_process, video_pre_process, generate_video, audio_process
import os
import re
import numpy as np
import threading
import websocket
from pydub import AudioSegment
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import cv2
import pygame
import hashlib
from fastapi import FastAPI
import uvicorn

app = FastAPI()

video_list = []

fay_ws = None
video_cache = {}

#增加MD5音频标记，避免重复生成视频
def hash_file_md5(filepath):
    md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        while True:
            data = f.read(65536)  # Read in 64kb chunks
            if not data:
                break
            md5.update(data)
    return md5.hexdigest()

def connet_fay():
    global video_list
    global video_cache
    def on_message(ws, message):
        if "audio" in message:
            message_dict = json.loads(message)
            aud_dir = message_dict["Data"]["Value"]
            aud_dir = aud_dir.replace("\\", "/")
            print('message:', aud_dir, type(aud_dir))
            basedir = ""
            for i in aud_dir.split("/"):
                basedir = os.path.join(basedir,i)
            basedir = basedir.replace(":",":\\")   
            num = time.time()
            new_path = r'./data/audio/aud_%d.wav'%num  #新路径                
            old_path = basedir                
 
            convert_mp3_to_wav(old_path, new_path) 
            audio_hash = hash_file_md5(new_path)
            if audio_hash in video_cache:
                video_list.append({"video": video_cache[audio_hash], "audio": new_path})
                print("视频已存在，直接播放。")
            else:
                audio_path = 'data/audio/aud_%d.wav' % num
                audio_process(audio_path)
                audio_path_eo = 'data/audio/aud_%d_eo.npy' % num
                video_path = 'data/video/results/ngp_%d.mp4' % num
                output_path = 'data/video/results/output_%d.mp4' % num
                generate_video(audio_path, audio_path_eo, video_path, output_path)
                video_list.append({"video" : output_path, "audio" : new_path})
                video_cache[audio_hash] = output_path

    def on_error(ws, error):
        print(f"Fay Error: {error}")
        fay_ws = None
        time.sleep(5)
        connect()

    def on_close(ws):
        print("Fay Connection closed")
        fay_ws = None

    def on_open(ws):
        print("Fay Connection opened")

    def connect():
        ws_url = "ws://127.0.0.1:10002"
        fay_ws = websocket.WebSocketApp(ws_url,
                                    on_message=on_message,
                                    on_error=on_error,
                                    on_close=on_close)
        fay_ws.on_open = on_open
        fay_ws.run_forever()
    connect()

@app.get("/audio_to_video/")
async def audio_to_video(file_path: str):
    aud_dir = file_path
    aud_dir = aud_dir.replace("\\", "/")
    print('message:', aud_dir, type(aud_dir))
    basedir = ""
    for i in aud_dir.split("/"):
        basedir = os.path.join(basedir,i)
    basedir = basedir.replace(":",":\\")   
    num = time.time()
    new_path = r'./data/audio/aud_%d.wav'%num  #新路径                
    old_path = basedir                

    convert_mp3_to_wav(old_path, new_path) 
    audio_hash = hash_file_md5(new_path)
    if audio_hash in video_cache:
        video_list.append({"video": video_cache[audio_hash], "audio": new_path})
        print("视频已存在，直接播放。")
    else:
        audio_path = 'data/audio/aud_%d.wav' % num
        audio_process(audio_path)
        audio_path_eo = 'data/audio/aud_%d_eo.npy' % num
        video_path = 'data/video/results/ngp_%d.mp4' % num
        output_path = 'data/video/results/output_%d.mp4' % num
        generate_video(audio_path, audio_path_eo, video_path, output_path)
        video_list.append({"video" : output_path, "audio" : new_path})
        video_cache[audio_hash] = output_path

    return {"code": 200}

def start_fastapi_server():
    uvicorn.run(app, host="0.0.0.0", port=8800)

def convert_mp3_to_wav(input_file, output_file):
    # 坑啊兄弟
    audio_extension = os.path.splitext(input_file)[1].lower()
    if audio_extension == "wav":
        audio = AudioSegment.from_wav(input_file)
    elif audio_extension == "mp3":
        audio = AudioSegment.from_mp3(input_file)
    else:
        audio = AudioSegment.from_file(input_file)
    audio.export(output_file, format='wav')


def play_video():
    global video_list
    video_path = None
    audio_path = None
    ret = None
    frame = None
    while True:
        if len(video_list) > 0:
            video_path = video_list[0].get("video")
            audio_path = video_list[0].get("audio")
            cap = cv2.VideoCapture(video_path)  # 打开视频文件
            video_list.pop(0)
        else:
            audio_path = None
            cap = None
            _, frame = cv2.VideoCapture("data/pretrained/train.mp4").read()

        if audio_path:
            threading.Thread(target=play_audio, args=[audio_path]).start()  # play audio
        # 循环播放视频帧
        while True:
            if cap:
                ret, frame = cap.read()
            if frame is not None:#没有传音频过来时显示train.mp4的第一帧，建议替换成大约1秒左右的视频
                cv2.imwrite('Fay-2d', frame)
                # 等待 38 毫秒
                cv2.waitKey(38)
            if not ret:
                break

def play_audio(audio_file):
    pygame.mixer.init()
    pygame.mixer.music.load(audio_file)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)
    pygame.mixer.music.stop()
if __name__ == '__main__':

    audio_pre_process()
    video_pre_process()

    # 注释掉原来的fay连接，你要用的话自己开回去吧
    threading.Thread(target=connet_fay, args=[]).start()
    # 创建并启动FastAPI服务的线程
    # threading.Thread(target=start_fastapi_server).start()

    play_video()


    
    

