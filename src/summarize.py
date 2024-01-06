import os
import re
import requests
import torch

import whisper
from pytube import YouTube
from moviepy.editor import *
from langdetect import detect

import tiktoken
from openai import OpenAI


# ----- downloading -----

def check_url(youtube_url: str) -> None:
    """Check url existence
    """
    res, msg = False, ''
    if re.match(r"^https://www.youtube.com/watch\?v=[a-zA-Z0-9_-]*$", youtube_url):
        try:
            response = requests.get(youtube_url, timeout=5)
            response.raise_for_status()
            if response.status_code == 200:
                res = True
        except requests.Timeout:
            msg = 'Request timed out'
        except requests.RequestException as e:
            msg = f'Request failed: {e}'
    else:
        msg = 'Wrong link'
    return res, msg


def video_title(youtube_url: str) -> str:
    """Retrieve the title of a YouTube video.
    """
    yt = YouTube(youtube_url)
    return yt.title


def download_audio(youtube_url: str, download_path: str, filename: str) -> None:
    """Download the audio from a YouTube video.
    """
    yt_ = YouTube(youtube_url)
    yt_.streams.filter(only_audio=True, 
                    file_extension='mp4').first().download(download_path, 
                                                           filename=filename)


def convert_mp4_to_mp3(input_path: str, output_path: str) -> None:
    """Convert an audio file from mp4 format to mp3.
    """
    audio_clip = AudioFileClip(input_path)
    audio_clip.write_audiofile(output_path, codec='mp3')
    audio_clip.close()
    os.remove(input_path)


# ----- transcribing -----

def transcribe(file_path: str, model_name="base", device=None) -> str:
    """Transcribe input audio file.
    """
    if not bool(device) and torch.cuda.is_available():
        device ='cuda'
    else:
        device ='cpu'

    model = whisper.load_model(model_name, device=device)
    result = model.transcribe(file_path)
    os.remove(file_path)
    return result['text']


# ----- summarizing -----

def summary_prompt(input_text: str) -> str:
    """
    Build prompt using input text of the video.
    """
    language = detect(input_text)

    if language == 'en':
        prompt = f"""
                Your task is to summarize a YouTube video clip. 
                Summarize the transcript bellow in triple backtick, minimum 30 words.
                Focus on the main aspects of what the video says.

                YouTube video clip transcript for summarizing: ```{input_text}```
                """
    elif language == 'de':
        prompt = f"""
                Ihre Aufgabe ist es, einen YouTube-Videoclip zusammenzufassen. 
                Fassen Sie das unten stehende Transkript in einem dreifachen Backtick zusammen, mindestens 30 Wörter.
                Konzentrieren Sie sich auf die wichtigsten Aspekte des Videos. Bitte tun Sie es auf Deutsch.

                YouTube-Videoclip-Transkript zum Zusammenfassen: ```{input_text}```
                """
    elif language == 'ru':
        prompt = f"""
                Твоя задача сгенерировать короткое саммари для расшифровки видео с YouTube.
                Сделай суммаризацию для текста ниже, заключенного в тройные квадратные скобки, минимум 30 слов.
                Сфокусируйся на главных аспектах о чем говорится в видео.

                Текст для суммаризации: [[[{input_text}]]]
                """
    else:
        prompt = f"""
                You have two tasks:
                Your main task is to summarize a YouTube video clip. 
                Summarize the transcript bellow in triple backtick, minimum 30 words.
                Focus on the main aspects of what the video says. 
                Please do so in English, regardless of the original language.
                Also detect the original language of the transcript and specify it at the beginning. 
            
                YouTube video clip for summarizing: ```{input_text}```
                """
    return prompt


def summarize_text(input_text: str) -> str:
    """Summarize input text of the video.
    """
    prompt = summary_prompt(input_text)
    
    model = "gpt-3.5-turbo" # gpt-4 "gpt-3.5-turbo"
    encoding = tiktoken.encoding_for_model(model)
    length = len(encoding.encode(prompt))
    if length < 4098:
        client = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
            )
        res = response.choices[0].message.content, None
    else:
        res = None, 'The video clip is too long.'

    return res
