import os
import requests
from requests.auth import HTTPDigestAuth
from flask import Flask, request, jsonify
import time

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

# Directory where videos will be saved
SAVE_DIR = "videos"
os.makedirs(SAVE_DIR, exist_ok=True)  # Create the directory if it doesn't exist

@app.route('/download_video', methods=['GET'])
def download_video():
    # Get start_time and end_time from the request parameters
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    if not start_time or not end_time:
        return jsonify({"error": "start_time and end_time parameters are required"}), 400

    # API URL
    url = f"http://{camera_ip}/cgi-bin/loadfile.cgi?action=startLoad&channel={channel}&startTime={start_time}&endTime={end_time}&subtype={subtype}&Types={file_type}"

    # Setup digest authentication
    auth = HTTPDigestAuth(username, password)

    try:
        # Send the GET request
        response = requests.get(url, auth=auth, stream=True)

        # Check if the request was successful
        if response.status_code == 200:
            # Generate a unique file name for saving the video
            file_name = f"video_{time.time()}.{file_type}"
            file_path = os.path.join(SAVE_DIR, file_name)

            # Save the video file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # Return the public file path
            public_url = f"/{SAVE_DIR}/{file_name}"
            return jsonify({"message": "Video downloaded", "file_path": public_url}), 200
        else:
            return jsonify({"error": f"Failed to download video. Status code: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=True)