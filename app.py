from flask import Flask, render_template, request, jsonify
import pytesseract
import cv2
import numpy as np

app = Flask(__name__)

# Caminho do Tesseract (Render já possui por padrão)
pytesseract.pytesseract.tesseract_cmd = "/usr/bin/tesseract"

@app.route('/')
def licenca():
    return render_template('licenca.html')

@app.route('/painel')
def painel():
    return render_template('index.html')

@app.route('/ocr', methods=['POST'])
def ocr():
    if 'image' not in request.files:
        return jsonify({"error": "Nenhuma imagem enviada."}), 400

    file = request.files['image']
    npimg = np.frombuffer(file.read(), np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binaria = cv2.threshold(gray, 120, 255, cv2.THRESH_BINARY)
    texto = pytesseract.image_to_string(binaria, lang='eng')
    numeros = [s for s in texto.split() if s.replace('.', '', 1).isdigit()]

    if numeros:
        numero = float(numeros[-1])
        return jsonify({"resultado": numero})
    else:
        return jsonify({"resultado": None})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
