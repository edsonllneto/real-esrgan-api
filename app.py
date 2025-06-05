from flask import Flask, request, jsonify
from PIL import Image
import base64
import io
from realesrgan import RealESRGAN
import torch

app = Flask(__name__)

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = RealESRGAN(device, scale=4)
model.load_weights('RealESRGAN_x4plus.pth', download=True)

@app.route("/inference", methods=["POST"])
def upscale():
    data = request.json.get("input", {})
    image_b64 = data.get("source_image")
    face_enhance = data.get("face_enhance", False)

    if not image_b64:
        return jsonify({"error": "Missing source_image"}), 400

    try:
        image_data = base64.b64decode(image_b64)
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        sr_image = model.predict(image)

        buffer = io.BytesIO()
        sr_image.save(buffer, format="PNG")
        buffer.seek(0)
        sr_b64 = base64.b64encode(buffer.read()).decode("utf-8")

        return jsonify({"result": sr_b64})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/", methods=["GET"])
def home():
    return "Real-ESRGAN API is running"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
