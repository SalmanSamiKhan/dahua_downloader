import os
import requests
from requests.auth import HTTPDigestAuth
from flask import Flask, request, jsonify, send_from_directory, Response
import time
from datetime import datetime

app = Flask(__name__)

# Dahua ONVIF camera details
camera_ip = "182.252.71.29"
username = "admin"
password = "Al@#2024"
channel = 1
subtype = 0
file_type = "mp4"

# Get the absolute path of the directory where videos will be saved
SAVE_DIR = os.path.join(os.getcwd(), "videos")
os.makedirs(SAVE_DIR, exist_ok=True)  # Create the directory if it doesn't exist

# Serve the videos directory statically
@app.route('/videos/<path:filename>')
def serve_video(filename):
    try:
        return send_from_directory(
            SAVE_DIR, filename, mimetype='video/mp4', as_attachment=True
        )
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route('/download_video', methods=['GET'])
def download_video():
    # Get start_time and end_time from the request parameters
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    channel = request.args.get('channel')

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
            current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            file_name = f"{current_time}.{file_type}"
            file_path = os.path.join(SAVE_DIR, file_name)

            # Save the video file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # Return the public file path
            # public_url = f"/videos/{file_name}"
            public_url = f"{request.host_url}videos/{file_name}"
            return jsonify({"message": "Video downloaded", "file_path": public_url}), 200
        else:
            return jsonify({"error": f"Failed to download video. Status code: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
