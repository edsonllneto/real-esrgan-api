from flask import Flask, request, jsonify, send_file
import os
from PIL import Image
import torch
from basicsr.archs.rrdbnet_arch import RRDBNet
from realesrgan import RealESRGANer

app = Flask(__name__)

# Inicializa o modelo
model_path = '/realesrgan/weights/RealESRGAN_x4plus.pth'

if not os.path.exists(model_path):
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    os.system(f"gdown --id 1rbSTGKAE-MTxBYHd-51l2hMOQPT_7EPy -O {model_path}")

# Rede base
model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=23, num_grow_ch=32, scale=4)

upscaler = RealESRGANer(
    scale=4,
    model_path=model_path,
    model=model,
    tile=0,
    tile_pad=10,
    pre_pad=0,
    half=True if torch.cuda.is_available() else False
)

@app.route('/')
def index():
    return "Real-ESRGAN API is running"

@app.route('/upscale', methods=['POST'])
def upscale():
    if 'image' not in request.files:
        return jsonify({'error': 'No image uploaded'}), 400

    img = Image.open(request.files['image']).convert('RGB')
    img.save('input.png')

    output, _ = upscaler.enhance(img)
    output_path = 'output.png'
    output.save(output_path)

    return send_file(output_path, mimetype='image/png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
