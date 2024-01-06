import os
from uuid import uuid4

import streamlit as st

from src.summarize import check_url, video_title
from src.summarize import convert_mp4_to_mp3, download_audio, transcribe
from src.summarize import summarize_text

assert os.environ["OPENAI_API_KEY"], "OPENAI_API_KEY not found!"

def main():
    st.title('Video Summarizer')
    
    # Paste url to youtube video
    youtube_url = st.text_input("Paste a link to a youtube (< 10 min) video:")

    transcribe_button = st.empty()
    title_placeholder = st.empty()
    progress_placeholder = st.empty()

    # transcription quality
    quality = st.toggle('Higher quality')
    if quality:
        model_name = 'medium'
    else:
        model_name = 'base'

    if transcribe_button.button('Summarize video'):
        # Download audio
        status, msg = check_url(youtube_url)

        if not status:
            st.error(msg)
            st.stop()

        try:
            transcribe_button.empty()
            title_placeholder.title(video_title(youtube_url))

            progress_placeholder.text("the video is downloading...")
            runtime_id = str(uuid4())
            os.makedirs('runtimes', exist_ok=True)
            filename = f'{runtime_id}.mp4'
            download_audio(youtube_url, 'runtimes', filename)
            mp4_track = f'runtimes/{filename}'
            mp3_track = f'runtimes/{runtime_id}.mp3'
            convert_mp4_to_mp3(mp4_track, mp3_track)

        except Exception as e:
            print(e)
            st.error('Please provide a correct link to the video!')
            transcribe_button.empty()
            title_placeholder.empty()
            progress_placeholder.empty()
            st.stop()

        # Transcribe
        try:
            progress_placeholder.text('Audio Recognition...')
            video_text = transcribe(mp3_track, model_name=model_name)
        except Exception as e:
            print(e)
            st.error('Recognition error. Please try again!')
            title_placeholder.empty()
            progress_placeholder.empty()
            st.stop()

        # Summarize
        try:
            progress_placeholder.text('Summarizing ...')
            summary, msg = summarize_text(video_text)
            if bool(summary):
                st.text_area("Summary:", summary, height=300)
            else:
                st.error(msg)
                title_placeholder.empty()
                progress_placeholder.empty()
                st.stop()
        except Exception as e:
            print(e)
            st.error('Summarization error. Please try again!')
            title_placeholder.empty()
            progress_placeholder.empty()
            st.stop()

        progress_placeholder.empty()
    
if __name__ == "__main__":
    main()
