import os
import moviepy.editor as mp
from pytube import YouTube
from tkinter import filedialog, Tk
from PIL import Image
import numpy as np
import re
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import googleapiclient.discovery

def clean_filename(name):
    # Remove characters not allowed in file names
    return re.sub(r'[<>:"/\\|?*]', '', name)

def resize_image(photo_path):
    img = Image.open(photo_path)
    img = img.resize((1280, 720))
    return np.array(img)  # Convert to numpy array

def create_videos(photo_path, audio_dir, output_dir, artist_name):
    photo_clip = mp.ImageClip(resize_image(photo_path))

    for audio_file in os.listdir(audio_dir):
        if audio_file.endswith('.mp3'):
            audio_path = os.path.join(audio_dir, audio_file)
            audio_clip = mp.AudioFileClip(audio_path)

            title = os.path.splitext(audio_file)[0]
            final_title = f"{artist_name} - {title}"

            video = mp.CompositeVideoClip([photo_clip.set_duration(audio_clip.duration)])
            video = video.set_audio(audio_clip)

            output_path = os.path.join(output_dir, f"{clean_filename(final_title)}.mp4")
            video.write_videofile(output_path, codec="libx264", fps=24, threads=4, ffmpeg_params=["-pix_fmt", "yuv420p"])

            print(f"Video created: {final_title}.mp4")

def upload_video(video_path, youtube, credentials_path):
    # Upload video
    request = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "10",  # Category ID for People & Blogs
                "title": os.path.splitext(os.path.basename(video_path))[0],
                "description": "Uploaded with Python" #to be changed by the user
            },
            "status": {
                "privacyStatus": "public"
            }
        },
        media_body=video_path
    )
    response = request.execute()
    print("Video uploaded successfully.")
    return response["id"]

def upload_to_youtube(video_dir, youtube, credentials_path):
    for video_file in os.listdir(video_dir):
        if video_file.endswith('.mp4'):
            video_path = os.path.join(video_dir, video_file)
            video_id = upload_video(video_path, youtube, credentials_path)
            print(f"Video uploaded to YouTube with ID: {video_id}")

def main():
    root = Tk()
    root.withdraw()

    photo_path = filedialog.askopenfilename(title="Select JPG Photograph")
    audio_dir = filedialog.askdirectory(title="Select Directory with MP3 Songs")
    output_dir = filedialog.askdirectory(title="Select Directory to Store MP4 Files")
    artist_name = input("Enter the artist name: ")

    artist_name = clean_filename(artist_name)

    create_videos(photo_path, audio_dir, output_dir, artist_name)

    upload_confirmation = input("Do you want to upload videos to YouTube? (yes/no): ")
    if upload_confirmation.lower() == 'yes':
        credentials_path = filedialog.askopenfilename(title="Select Credentials File")

        # Load credentials
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
        credentials = flow.run_local_server()

        # Authenticate and create YouTube service
        youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

        upload_to_youtube(output_dir, youtube, credentials_path)

if __name__ == "__main__":
    main()
