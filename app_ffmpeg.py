import os
import requests
from requests.auth import HTTPDigestAuth
from flask import Flask, request, jsonify, send_from_directory
import time
from datetime import datetime
import pytz
import subprocess  # To run ffmpeg commands

app = Flask(__name__)

# Dahua ONVIF camera details
camera_ip = "182.252.71.29"
username = "admin"
password = "Al@#2024"
channel = 1
subtype = 0
file_type = "mp4"

# Time zone setup (camera's time zone is UTC+6)
CAMERA_TIMEZONE = pytz.timezone("Asia/Dhaka")  # UTC+06:00

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

    try:
        # Parse the input times assuming they are in the camera's time zone (UTC+6)
        start_time_camera = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
        end_time_camera = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

        # No need to convert time to a different timezone since the camera is already in UTC+6

        # Format the times in the format the camera expects (YYYYMMDDTHHMMSS)
        start_time_camera_str = start_time_camera.strftime('%Y-%m-%d %H:%M:%S')
        end_time_camera_str = end_time_camera.strftime('%Y-%m-%d %H:%M:%S')

    except ValueError:
        return jsonify({"error": "Invalid time format. Use 'YYYY-MM-DD HH:MM:SS'"}), 400

    # API URL for downloading video using camera's adjusted times
    url = (f"http://{camera_ip}/cgi-bin/loadfile.cgi?action=startLoad&channel={channel}"
           f"&startTime={start_time_camera_str}&endTime={end_time_camera_str}"
           f"&subtype={subtype}&Types={file_type}")

    # Setup digest authentication
    auth = HTTPDigestAuth(username, password)

    try:
        # Send the GET request
        response = requests.get(url, auth=auth, stream=True)

        # Check if the request was successful and return a failure if the times mismatch
        if response.status_code == 200:
            # Generate a unique file name with a human-readable timestamp format
            current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
            file_name = f"{current_time}_raw.{file_type}"
            file_path = os.path.join(SAVE_DIR, file_name)

            # Save the video file
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

            # Get the file size to ensure that some data was downloaded
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                os.remove(file_path)  # Delete the empty file
                return jsonify({"error": "No video data available for the requested time range."}), 404

            # Convert the raw video to a universally supported MP4 format using ffmpeg
            output_file_name = f"{current_time}.mp4"
            output_file_path = os.path.join(SAVE_DIR, output_file_name)

            ffmpeg_command = [
                "ffmpeg", "-i", file_path, "-c:v", "libx264", "-c:a", "aac", "-strict", "experimental", output_file_path
            ]

            subprocess.run(ffmpeg_command, check=True)

            # Delete the raw file after conversion
            os.remove(file_path)

            # Return the public file path using request.host_url to construct the full URL
            public_url = f"{request.host_url}videos/{output_file_name}"
            return jsonify({"message": "Video downloaded and converted", "file_path": public_url}), 200
        else:
            return jsonify({"error": f"Failed to download video. Status code: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
