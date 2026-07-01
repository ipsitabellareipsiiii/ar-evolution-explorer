import os
import io
import socket
import base64
import json
from flask import Flask, render_template, request, jsonify
import qrcode
app = Flask(__name__)
# Load animal evolution datasets
def load_animals():
    data_path = os.path.join(os.path.dirname(__file__), 'data', 'animals.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)
# Helper to automatically determine local IP for Wi-Fi testing
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"
@app.route('/')
def index():
    animals = load_animals()
    return render_template('index.html', animals=animals)
@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    req_data = request.get_json()
    animal_id = req_data.get('animal_id')
    animals = load_animals()
    if animal_id not in animals:
        return jsonify({"error": "Animal profile not found"}), 404
    animal = animals[animal_id]
    # Dynamically select URL depending on the hosting environment
    # 1. Check if configured with an environment variable (e.g., when deployed on Render)
    base_url = os.environ.get('BASE_URL')
    
    if not base_url:
        # 2. Local fallback: use the actual local network IP so devices on the same Wi-Fi can scan it
        local_ip = get_local_ip()
        base_url = f"http://{local_ip}:5000"
    ar_url = f"{base_url}/ar/{animal_id}"
    print(f"[QR Code Generated] Redirecting to: {ar_url}")
    # Generate QR Code image using standard package
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(ar_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0d1214", back_color="#ffffff")
    # Save to binary memory stream (avoids writing to disk)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    # Encode binary image to base64 data uri format
    img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    qr_data_uri = f"data:image/png;base64,{img_b64}"
    return jsonify({
        "animal_name": animal['name'],
        "qr_code": qr_data_uri,
        "ar_url": ar_url
    })
@app.route('/ar/<animal_id>')
def ar_view(animal_id):
    animals = load_animals()
    if animal_id not in animals:
        return "Animal profile not found", 404
        
    return render_template('ar_view.html', animal=animals[animal_id])
if __name__ == '__main__':
    # Determine local host interface IP on run
    ip_addr = get_local_ip()
    print("\n" + "="*60)
    print(f"🚀 AR Evolution Explorer Running Locally!")
    print(f"👉 Open desktop homepage: http://localhost:5000")
    print(f"👉 Local WiFi network IP: http://{ip_addr}:5000")
    print("="*60 + "\n")
    
    # Run on all network interfaces (0.0.0.0) so phone can connect over Wi-Fi
    app.run(host='0.0.0.0', port=5000, debug=True)