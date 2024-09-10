import requests
from requests.auth import HTTPDigestAuth
import time

# Dahua ONVIF camera details
camera_ip = "182.252.71.29"
username = "admin"
password = "Al@#2024"
channel = 1
start_time = "2024-09-05 16:00:00"
end_time = "2024-09-05 16:01:00"
subtype = 0
file_type = "mp4"

# API URL
url = f"http://{camera_ip}/cgi-bin/loadfile.cgi?action=startLoad&channel={channel}&startTime={start_time}&endTime={end_time}&subtype={subtype}&Types={file_type}"

# Setup digest authentication
auth = HTTPDigestAuth(username, password)

try:
    # Send the GET request
    response = requests.get(url, auth=auth, stream=True)

    # Check if the request was successful
    if response.status_code == 200:
        # File name for saving the video
        file_name = f"video_{start_time.replace(' ', '_')}_to_{end_time.replace(' ', '_')}.{file_type}"
        file_name=f'{time.time()}.{file_type}'

        # Save the video file
        with open(file_name, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
        
        print(f"Video downloaded and saved as {file_name}")
    else:
        print(f"Failed to download video. Status code: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")