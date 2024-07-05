import psutil
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import base64
from PIL import Image
import read_image
from time import asctime as asc
from keys import v
from fastapi.responses import HTMLResponse

app = FastAPI()

variables = {
    "API_KEY": v,
    "filename": "fastkwt.jpeg",
    "length": 100,
    "width": 100
}

# Allow CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/process_image/{API_KEY}')
async def process_image(API_KEY: str, request: Request):
    temp_obj = psutil.sensors_temperatures()
    core_temp_len_obj = temp_obj['coretemp']
    temp_append = [core.current for core in core_temp_len_obj]

    for temp in temp_append:
        print(f"CPU temp {temp} C")

    api_success = False
    try:
        for key in variables['API_KEY']:
            if API_KEY == key:
                api_success = True

                request_json = await request.json()
                image_data_url = request_json.get('image_data')

                if image_data_url:
                    data = base64.b64decode(image_data_url.split(',')[1])
                    
                    with open(variables['filename'], 'wb') as f:
                        f.write(data)
                    
                    image = Image.open(variables['filename'])
                    new_image_size = image.resize((variables['length'], variables['width']))
                    new_image_size.save(variables['filename'])
                    
                    response = read_image.generate_response([variables['filename']])

                    os.remove(variables['filename'])

                    return JSONResponse(content={"response": response, "time": asc()}, status_code=200)
                else:
                    raise HTTPException(status_code=400, detail="No image data received")
    except Exception as e:
        print(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process image")

    if not api_success:
        raise HTTPException(status_code=401, detail="Unauthorized API key")

@app.get("/", response_class=HTMLResponse)
async def root():
    return '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Capture</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
        }
        #video-container {
            width: 100%;
            max-width: 600px;
            margin-bottom: 20px;
            position: relative;
        }
        #video-feed {
            width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        }
        #capture-btn {
            display: block;
            margin: 20px auto;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            transition: background-color 0.3s ease;
        }
        #capture-btn:hover {
            background-color: #0056b3;
        }
        #response {
            margin-top: 20px;
            font-size: 16px;
            color: #333;
        }
        #loading-indicator {
            display: none;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 18px;
            color: white;
            background-color: rgba(0, 0, 0, 0.7);
            padding: 10px 20px;
            border-radius: 5px;
        }
        #camera-select {
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div id="video-container">
        <video id="video-feed" autoplay playsinline></video>
        <div id="loading-indicator">Processing...</div>
    </div>
    <select id="camera-select"></select>
    <button id="capture-btn">Capture Photo</button>
    <p id='response'></p>

    <script>
        const videoElement = document.getElementById('video-feed');
        const captureButton = document.getElementById('capture-btn');
        const loadingIndicator = document.getElementById('loading-indicator');
        const cameraSelect = document.getElementById('camera-select');

        // Access the camera and display the video feed
        async function startCamera(deviceId = null) {
            const constraints = {
                video: deviceId ? { deviceId: { exact: deviceId } } : { facingMode: "environment" }
            };

            try {
                const stream = await navigator.mediaDevices.getUserMedia(constraints);
                videoElement.srcObject = stream;
            } catch (err) {
                console.error('Error accessing camera:', err);
            }
        }
// Populate camera selection dropdown
async function getCameras() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(device => device.kind === 'videoinput');

    cameraSelect.innerHTML = '';
    videoDevices.forEach((device, index) => {
        const option = document.createElement('option');
        option.value = device.deviceId;
        option.text = device.label || `Camera ${index + 1}`;
        cameraSelect.appendChild(option);
    });

    // Select the first camera by default
    if (videoDevices.length > 0) {
        startCamera(videoDevices[0].deviceId);
    }
}
        // Capture a photo from the video feed
        async function capturePhoto() {
            // Show loading indicator
            loadingIndicator.style.display = 'block';

            // Pause the video feed
            videoElement.pause();

            const canvas = document.createElement('canvas');
            canvas.width = videoElement.videoWidth;
            canvas.height = videoElement.videoHeight;
            const context = canvas.getContext('2d');
            context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

            // Convert the canvas to a data URL and send to backend
            const imageDataURL = canvas.toDataURL('image/jpeg');
            const APIKEY = 'd9bcad0fb03c0b28adb4c6e2b755bbb0';

            try {
                const response = await fetch(`/process_image/${APIKEY}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ image_data: imageDataURL }),
                });

                const data = await response.json();
                console.log('Response from server:', data);
                write_data_to_response_field(data['response'], data['time']);
            } catch (error) {
                console.error('Error sending image data:', error);
            } finally {
                // Hide loading indicator
                loadingIndicator.style.display = 'none';

                // Resume the video feed
                videoElement.play();
            }
        }

        // Event listeners
        captureButton.addEventListener('click', capturePhoto);
        cameraSelect.addEventListener('change', (event) => {
            const deviceId = event.target.value;
            startCamera(deviceId);
        });

        // Start camera feed and populate camera selection when the page loads
        getCameras().then(() => {
            startCamera(cameraSelect.value);
        });

        function write_data_to_response_field(response, time) {
            let definition_response = document.getElementById('response');
            definition_response.innerHTML = `
            <h1>Response processed!</h1> <br>
            Time: ${time}. \n <br>
            Response: ${response} \n <br>
            Model: llava
            `;
            return 200;
        }

        function reset_response_field() {
            let definition_response = document.getElementById('response');
            definition_response.innerHTML = "";
            return 200;
        }
    </script>
</body>
</html>
    '''
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000, ssl_keyfile="mykey.key", ssl_certfile="mycert.crt")
    