import cv2
import numpy as np
import mss
import pytesseract
import time
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

# 🔧 Caminho do executável Tesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 🔥 Configurar Firebase (baixe seu arquivo JSON de credenciais no console Firebase)
import json, os
firebase_key = os.environ.get("FIREBASE_KEY")
cred = credentials.Certificate(json.loads(firebase_key))
firebase_admin.initialize_app(cred)
db = firestore.client()

# 📸 Função de captura
def capturar_texto(regiao):
    with mss.mss() as sct:
        imagem = np.array(sct.grab(regiao))
        cinza = cv2.cvtColor(imagem, cv2.COLOR_BGR2GRAY)
        _, binaria = cv2.threshold(cinza, 120, 255, cv2.THRESH_BINARY)
        texto = pytesseract.image_to_string(binaria, lang='eng')
        return texto.strip(), binaria

# 📍 Selecionar área uma vez
def selecionar_area():
    with mss.mss() as sct:
        monitor = sct.monitors[1]
        tela = np.array(sct.grab(monitor))
        r = cv2.selectROI("Selecione a área para leitura", tela, showCrosshair=True)
        cv2.destroyWindow("Selecione a área para leitura")
        x, y, w, h = map(int, r)
        return {"top": y, "left": x, "width": w, "height": h}

def main():
    print("🤖 Robô de leitura e envio ao Firebase iniciado!")
    regiao = selecionar_area()
    ultimo_resultado = ""
    lendo = False
    rodada = 1

    while True:
        texto, imagem = capturar_texto(regiao)
        numeros = ''.join([c for c in texto if c.isdigit() or c == '.'])

        if numeros:
            lendo = True
            print(f"Lendo: {numeros}")
            ultimo_resultado = numeros
        elif lendo:
            # Quando parar de ler, envia o último número
            print(f"✅ Rodada {rodada} finalizada! Resultado: {ultimo_resultado}")

            # Salva no Firebase
            db.collection("resultados").document("ultimo").set({
                "valor": ultimo_resultado,
                "hora": datetime.now().strftime("%H:%M:%S"),
                "data": datetime.now().strftime("%Y-%m-%d")
            })

            # Histórico opcional
            db.collection("historico").add({
                "rodada": rodada,
                "resultado": ultimo_resultado,
                "timestamp": datetime.now()
            })

            lendo = False
            rodada += 1
            time.sleep(2)

        cv2.imshow("Leitura ao vivo", imagem)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
