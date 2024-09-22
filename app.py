from flask import Flask, render_template, request, jsonify
from fer import FER
import cv2
import numpy as np
import base64
from io import BytesIO
from PIL import Image

app = Flask(__name__)
detector = FER(mtcnn=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    if 'image' not in request.files and 'image' not in request.form:
        return jsonify({'error': 'No image data received'}), 400
    
    if 'image' in request.files:
        file = request.files['image']
        img = Image.open(file.stream)
    else:
        # Handle base64 encoded image from camera
        image_data = request.form['image'].split(',')[1]
        img = Image.open(BytesIO(base64.b64decode(image_data)))
    
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    
    emotions = detector.detect_emotions(img)
    
    if not emotions:
        return jsonify({'error': 'No face detected in the image'}), 400
    
    # Process the first detected face
    face = emotions[0]
    emotions_dict = face['emotions']
    
    # Draw rectangle around the face
    x, y, w, h = face['box']
    cv2.rectangle(img, (x, y), (x+w, y+h), (0, 255, 0), 2)
    
    # Add text for the dominant emotion
    dominant_emotion = max(emotions_dict, key=emotions_dict.get)
    cv2.putText(img, f"{dominant_emotion}: {emotions_dict[dominant_emotion]:.2f}", 
                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
    
    # Convert image to base64 for sending back to client
    _, buffer = cv2.imencode('.jpg', img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return jsonify({
        'image_url': f'data:image/jpeg;base64,{img_base64}',
        'emotions': emotions_dict
    })

if __name__ == '__main__':
    app.run(debug=True)