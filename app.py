from flask import Flask, request, render_template, jsonify
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

app = Flask(__name__)

# =======================================
# CONFIG WHATSAPP API
# =======================================
WHATSAPP_TOKEN = "EAALl2GJDMpMBPZBu8NmFIjWvqIDKJh4B1QlNsmG7n557ffCdCnNeXZBg1bR2bGFWo1CNZCXL5jiYXpfPZCZC8ZBGMbWUXw7vx4HykAPZBJ4bWczUa8ZClwKrPbCZBXgkW9DMemDkIqqCVO7BFNkoxZBjQu7nLQIkCUmu17J9zG8ZA5fgRX5RaK4ORLEdcYOo7vuRH1DZCwZDZD"
PHONE_ID = "848088375057819"
VERIFY_TOKEN = "meu_token_webhook"


# =======================================
# FIREBASE ADMIN
# =======================================
try:
    firebase_key = os.environ.get("FIREBASE_KEY")

    if firebase_key:
        cred = credentials.Certificate(json.loads(firebase_key))
    else:
        cred = credentials.Certificate("firebase-key.json")

    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("🔥 Firebase conectado no servidor!")

except Exception as e:
    print("❌ Erro ao conectar Firebase:", e)
    db = None


# =======================================
# HOME (JOGO)
# =======================================
@app.route('/')
def home():
    return render_template('index.html')


# =======================================
# PAINEL ADMIN SECRETO
# =======================================
@app.route('/admin')
def admin():
    return render_template('painel.html')


# =======================================
# VERIFICAÇÃO DO WEBHOOK (GET)
# =======================================
@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403


# ======================================================
# RECEBER MENSAGENS DO WHATSAPP (POST)
# ======================================================
@app.route('/webhook', methods=['POST'])
def receber_mensagem():
    data = request.get_json()

    print("\n📩 MENSAGEM RECEBIDA ==================")
    print(json.dumps(data, indent=4))

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages")

        if messages:
            msg = messages[0]
            numero = msg["from"]  # Ex: "5511987654321"

            # ---- SALVAR CONTATO ----
            db.collection("contatos").document(numero).set({
                "numero": numero
            }, merge=True)

            # ---- SALVAR MENSAGEM ----
            if "text" in msg:
                texto = msg["text"]["body"]

                db.collection("contatos").document(numero).collection("mensagens").add({
                    "de": numero,
                    "texto": texto
                })

                print(f"📲 De: {numero} | 💬 {texto}")

                enviar_whatsapp(numero, "Recebi sua mensagem, obrigado! 🔥")

    except Exception as e:
        print("❌ ERRO ao processar:", e)

    return jsonify({"status": "recebido"}), 200


# ======================================================
# FUNÇÃO ENVIAR MENSAGEM WHATSAPP
# ======================================================
def enviar_whatsapp(destino, mensagem):
    url = f"https://graph.facebook.com/v19.0/{PHONE_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": destino,
        "text": {"body": mensagem}
    }

    r = requests.post(url, json=payload, headers=headers)

    print("📤 Resposta do WhatsApp:", r.text)


# ======================================================
# ROTA: ROBÔ LOCAL ENVIA SINAL
# ======================================================
@app.route('/enviar_sinal', methods=['POST'])
def enviar_sinal():
    data = request.get_json()
    resultado = data.get("resultado")

    if not resultado:
        return jsonify({"erro": "resultado obrigatório"}), 400

    print(f"\n🚀 Recebi sinal do robô local: {resultado}")

    # Buscar todos os contatos registrados
    contatos = db.collection("contatos").stream()

    enviados = 0

    for c in contatos:
        numero = c.id
        enviar_whatsapp(numero, f"📊 NOVO SINAL DETECTADO: {resultado}x")
        enviados += 1

    print(f"🔥 Sinal enviado para {enviados} contatos!")

    return jsonify({"status": "ok", "enviados": enviados}), 200


# ======================================================
# ROTA: LISTAR MENSAGENS PARA O PAINEL
# ======================================================
@app.route('/mensagens')
def listar_mensagens():
    contatos_ref = db.collection("contatos").stream()

    dados = {}

    for contato in contatos_ref:
        numero = contato.id
        mensagens = []

        msgs_ref = db.collection("contatos").document(numero).collection("mensagens").stream()

        for m in msgs_ref:
            mensagens.append(m.to_dict())

        dados[numero] = mensagens

    return jsonify(dados)


# =======================================
# START SERVIDOR
# =======================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
