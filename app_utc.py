import os
import requests
import subprocess
from requests.auth import HTTPDigestAuth
from flask import Flask, request, jsonify, send_from_directory, Response
import time
from datetime import datetime
import pytz

from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Dahua ONVIF camera details from .env
camera_ip = os.getenv("CAMERA_IP")
username = os.getenv("CAMERA_USERNAME")
password = os.getenv("CAMERA_PASSWORD")
# channel = 1
# subtype = 0
file_type = "mp4"

# Get the absolute path of the directory where videos will be saved
SAVE_DIR = os.path.join(os.getcwd(), "videos")
os.makedirs(SAVE_DIR, exist_ok=True)  # Create the directory if it doesn't exist

# Serve the videos directory statically
@app.route('/videos/<path:filename>')
def serve_video(filename):
    try:
        return send_from_directory(
            SAVE_DIR, filename, mimetype='video/mp4', as_attachment=False
        )
    except FileNotFoundError:
        return jsonify({"error": "File not found"}), 404

@app.route('/download_video', methods=['GET'])
def download_video():
    # Get start_time and end_time from the request parameters
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')
    channel = request.args.get('channel')
    subtype = request.args.get('subtype')
    
    # Define the format your input times are in
    time_format = '%Y-%m-%d %H:%M:%S'

    # Parse the local time strings to datetime objects
    local_start_time = datetime.strptime(start_time, time_format)
    local_end_time = datetime.strptime(end_time, time_format)

    # Define the local timezone, for example, 'Asia/Dhaka' for Bangladesh Standard Time
    local_tz = pytz.timezone('Asia/Dhaka')

    # Localize the naive datetime objects (assuming they are in the local timezone)
    localized_start_time = local_tz.localize(local_start_time)
    localized_end_time = local_tz.localize(local_end_time)

    # Convert to UTC
    start_time = localized_start_time.astimezone(pytz.utc)
    end_time = localized_end_time.astimezone(pytz.utc)
    
    print(f'utc_start_time: {start_time}, utc_end_time: {end_time}')

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
            original_file_name = f"{current_time}.{file_type}"
            original_file_path = os.path.join(SAVE_DIR, original_file_name)

            # Save the video file
            with open(original_file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            
                        # Prepare the new file name for faststart processing
            processed_file_name = f"{current_time}_processed.{file_type}"
            processed_file_path = os.path.join(SAVE_DIR, processed_file_name)

            # Run ffmpeg to move moov atom to the start of the file
            ffmpeg_command = [
                'ffmpeg', '-i', original_file_path, '-movflags', 'faststart', '-c', 'copy', processed_file_path
            ]
            subprocess.run(ffmpeg_command, check=True)

            # Delete the original file after processing
            os.remove(original_file_path)
                        
            # Get the file size to ensure that some data was downloaded
            file_size = os.path.getsize(processed_file_path)
            if file_size == 0:
                os.remove(processed_file_path)  # Delete the empty file
                return jsonify({"error": "No video data available for the requested time range."}), 404

            # Return the public file path
            public_url = f"{request.host_url}videos/{processed_file_name}"
            print(f"Success response: {response}")
            return jsonify({"message": "Video downloaded", "stream_url": public_url}), 200
        else:
            print(f"Failed to download video. Status code: {response}")
            return jsonify({"error": f"Failed to download video. Status code: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
