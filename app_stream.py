# import os
# import requests
# import subprocess
# import threading
# from requests.auth import HTTPDigestAuth
# from flask import Flask, request, jsonify, send_from_directory, Response
# from datetime import datetime

# app = Flask(__name__)

# # Dahua ONVIF camera details
# camera_ip = "182.252.71.29"
# username = "admin"
# password = "Al@#2024"
# channel = 1
# subtype = 0
# file_type = "mp4"
# start_time = "2024-09-10%2016:30:00"
# end_time = "2024-09-10%2016:37:00"

# # Get the absolute path of the directory where videos will be saved
# SAVE_DIR = os.path.join(os.getcwd(), "videos")
# os.makedirs(SAVE_DIR, exist_ok=True)  # Create the directory if it doesn't exist

# # Serve the videos directory statically
# @app.route('/videos/<path:filename>')
# def serve_video(filename):
#     try:
#         return send_from_directory(SAVE_DIR, filename, as_attachment=False)
#     except FileNotFoundError:
#         return jsonify({"error": "File not found"}), 404

# # Function to download and process video in the background
# def download_and_process_video(original_file_path, processed_file_path, url, auth):
#     try:
#         # Send the GET request to download the video
#         response = requests.get(url, auth=auth, stream=True)

#         if response.status_code == 200:
#             # Save the video file
#             with open(original_file_path, 'wb') as f:
#                 for chunk in response.iter_content(chunk_size=1024):
#                     if chunk:
#                         f.write(chunk)

#             # Run ffmpeg to move moov atom to the start of the file
#             ffmpeg_command = [
#                 'ffmpeg', '-i', original_file_path, '-movflags', 'faststart', '-c', 'copy', processed_file_path
#             ]
#             subprocess.run(ffmpeg_command, check=True)

#             # Delete the original file after processing
#             os.remove(original_file_path)

#             # Check if the processed file has content
#             file_size = os.path.getsize(processed_file_path)
#             if file_size == 0:
#                 os.remove(processed_file_path)
#         else:
#             print(f"Failed to download video. Status code: {response.status_code}")

#     except Exception as e:
#         print(f"Error downloading and processing video: {str(e)}")

# @app.route('/download_video', methods=['GET'])
# def download_video():
#     # API URL
#     url = f"http://{camera_ip}/cgi-bin/loadfile.cgi?action=startLoad&channel={channel}&startTime={start_time}&endTime={end_time}&subtype={subtype}&Types={file_type}"

#     # Setup digest authentication
#     auth = HTTPDigestAuth(username, password)

#     # Generate a unique file name for saving the video
#     current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
#     original_file_name = f"{current_time}.{file_type}"
#     original_file_path = os.path.join(SAVE_DIR, original_file_name)

#     # Prepare the new file name for faststart processing
#     processed_file_name = f"{current_time}_processed.{file_type}"
#     processed_file_path = os.path.join(SAVE_DIR, processed_file_name)

#     # Start downloading and processing the video in a separate thread
#     download_thread = threading.Thread(
#         target=download_and_process_video,
#         args=(original_file_path, processed_file_path, url, auth)
#     )
#     download_thread.start()

#     # Return the public file path immediately
#     public_url = f"http://127.0.0.1:5001/videos/{processed_file_name}"
#     return jsonify({"message": "Video download started", "file_path": public_url}), 200

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=True)


# import os
# import requests
# from requests.auth import HTTPDigestAuth
# from flask import Flask, Response, jsonify

# app = Flask(__name__)

# # Dahua ONVIF camera details
# camera_ip = "182.252.71.29"
# username = "admin"
# password = "Al@#2024"
# channel = 1
# subtype = 0
# file_type = "mp4"
# start_time = "2024-09-10%2016:30:00"
# end_time = "2024-09-10%2016:35:00"

# # Stream video to the browser while downloading
# @app.route('/stream_video', methods=['GET'])
# def stream_video():
#     # API URL
#     url = f"http://{camera_ip}/cgi-bin/loadfile.cgi?action=startLoad&channel={channel}&startTime={start_time}&endTime={end_time}&subtype={subtype}&Types={file_type}"
    
#     # Setup digest authentication
#     auth = HTTPDigestAuth(username, password)
    
#     try:
#         # Send GET request to download video in chunks
#         response = requests.get(url, auth=auth, stream=True)

#         # Check if the request was successful
#         if response.status_code == 200:
#             # Stream video chunks to the client as they are downloaded
#             def generate():
#                 for chunk in response.iter_content(chunk_size=1024):
#                     if chunk:
#                         yield chunk

#             # Return a streaming response
#             return Response(generate(), content_type=f'video/{file_type}')

#         else:
#             return jsonify({"error": f"Failed to download video. Status code: {response.status_code}"}), 500

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=True)


# import os
# import requests
# import subprocess
# from requests.auth import HTTPDigestAuth
# from flask import Flask, jsonify, Response

# app = Flask(__name__)

# # Dahua ONVIF camera details
# camera_ip = "182.252.71.29"
# username = "admin"
# password = "Al@#2024"
# channel = 1
# subtype = 0
# file_type = "mp4"
# start_time = "2024-09-10%2016:30:00"
# end_time = "2024-09-10%2016:35:00"

# # Stream video while processing it with ffmpeg
# @app.route('/stream_video', methods=['GET'])
# def stream_video():
#     # API URL to fetch video from the camera
#     url = f"http://{camera_ip}/cgi-bin/loadfile.cgi?action=startLoad&channel={channel}&startTime={start_time}&endTime={end_time}&subtype={subtype}&Types={file_type}"

#     # Setup digest authentication
#     auth = HTTPDigestAuth(username, password)

#     try:
#         # Send GET request to download video from the camera
#         response = requests.get(url, auth=auth, stream=True)

#         # Check if the request was successful
#         if response.status_code == 200:
#             # Run ffmpeg to add 'faststart' flag on the fly for streamable video
#             ffmpeg_command = [
#                 'ffmpeg', 
#                 '-i', 'pipe:0',                 # Input from the pipe (camera stream)
#                 '-movflags', 'faststart',       # Add faststart for browser streaming
#                 '-c', 'copy',                   # Copy without re-encoding
#                 '-f', 'mp4',                    # Output format mp4
#                 'pipe:1'                        # Output to pipe for streaming
#             ]

#             # Start ffmpeg process
#             ffmpeg_process = subprocess.Popen(ffmpeg_command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#             # Stream video chunks to ffmpeg for processing and conversion
#             def generate():
#                 try:
#                     for chunk in response.iter_content(chunk_size=1024):
#                         if chunk:
#                             # Write chunk to ffmpeg stdin for conversion
#                             ffmpeg_process.stdin.write(chunk)
#                             # Read the processed video from ffmpeg stdout
#                             data = ffmpeg_process.stdout.read(1024)
#                             if data:
#                                 # Yield the converted chunk to the client
#                                 yield data
#                 except Exception as e:
#                     ffmpeg_process.terminate()
#                     print(f"Error during streaming: {e}")

#             # Return the video stream with 'faststart' applied
#             return Response(generate(), content_type='video/mp4')

#         else:
#             return jsonify({"error": f"Failed to download video. Status code: {response.status_code}"}), 500

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5001, debug=True)



import os
import requests
import subprocess
from requests.auth import HTTPDigestAuth
from flask import Flask, jsonify, Response, url_for
from datetime import datetime

app = Flask(__name__)

# Dahua ONVIF camera details
camera_ip = "182.252.71.29"
username = "admin"
password = "Al@#2024"
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
