import os
import requests
import subprocess
from requests.auth import HTTPDigestAuth
from flask import Flask, jsonify, Response, url_for
from datetime import datetime
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Dahua ONVIF camera details from .env
camera_ip = os.getenv("CAMERA_IP")
username = os.getenv("CAMERA_USERNAME")
password = os.getenv("CAMERA_PASSWORD")
channel = 1
subtype = 0
file_type = "mp4"
start_time = "2024-09-10%2016:30:00"
end_time = "2024-09-10%2016:32:00"

# Directory to save videos
SAVE_DIR = os.path.join(os.getcwd(), "videos")
os.makedirs(SAVE_DIR, exist_ok=True)  # Create the directory if it doesn't exist

@app.route('/download_video', methods=['GET'])
def download_video():
    try:
        # Generate unique file name for the video
        current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        file_name = f"{current_time}.{file_type}"
        file_path = os.path.join(SAVE_DIR, file_name)

        # Return the URL where the video will be streamed
        stream_url = url_for('stream_video', filename=file_name, _external=True)

        # Start the background process for downloading and processing
        process_video_download(file_name, file_path)

        # Return the stream URL to the user so they can start watching
        return jsonify({"message": "Video is being processed", "stream_url": stream_url}), 202

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/stream/<path:filename>', methods=['GET'])
def stream_video(filename):
    file_path = os.path.join(SAVE_DIR, filename)

    def generate():
        # Streaming the file in chunks
        with open(file_path, 'rb') as f:
            while True:
                data = f.read(1024)
                if not data:
                    break
                yield data

    return Response(generate(), content_type='video/mp4')

def process_video_download(file_name, file_path):
    """Downloads the video from the camera and processes it using ffmpeg in the background."""
    # API URL to fetch video from the camera
    url = f"http://{camera_ip}/cgi-bin/loadfile.cgi?action=startLoad&channel={channel}&startTime={start_time}&endTime={end_time}&subtype={subtype}&Types={file_type}"

    auth = HTTPDigestAuth(username, password)

    try:
        # Send GET request to download video from the camera
        response = requests.get(url, auth=auth, stream=True)

        # Check if the request was successful
        if response.status_code == 200:
            # Save the downloaded video
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # Run ffmpeg to add 'faststart' flag for streaming
            ffmpeg_command = [
                'ffmpeg',
                '-i', file_path,
                '-movflags', 'faststart',      # Make the video streamable
                '-c', 'copy',                  # Copy without re-encoding
                file_path
            ]
            subprocess.run(ffmpeg_command, check=True)

        else:
            print(f"Failed to download video. Status code: {response.status_code}")

    except Exception as e:
        print(f"Error downloading video: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
