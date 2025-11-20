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
# RECEBER MENSAGENS DO WHATSAPP
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
            numero = msg["from"]

            # identificar texto em QUALQUER estrutura
            texto = None
            
           # identificar texto em QUALQUER estrutura
texto = None
            
if "text" in msg and "body" in msg["text"]:
    texto = msg["text"]["body"]
elif msg.get("type") == "text" and "text" in msg and "body" in msg["text"]:
    texto = msg["text"]["body"]
elif "message" in msg:
    texto = msg["message"].get("body")

if not texto:
    texto = "(mensagem sem texto)"


            # >>> salvar número
            db.collection("chats").document(numero).set({
                "numero": numero
            }, merge=True)

            # >>> salvar mensagem
            db.collection("chats").document(numero).collection("mensagens").add({
                "mensagem": texto,
                "remetente": "cliente",
                "timestamp": firestore.SERVER_TIMESTAMP
            })

            print(f"📲 De: {numero} | 💬 {texto}")

            # responder
            enviar_whatsapp(numero, "Recebi sua mensagem, obrigado! 🔥")

    except Exception as e:
        print("❌ ERRO:", e)

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
    print("📤 Enviada:", r.text)


# ======================================================
# ENVIAR SINAL PARA TODOS (ROBÔ LOCAL)
# ======================================================
@app.route('/enviar_sinal', methods=['POST'])
def enviar_sinal():
    data = request.get_json()
    resultado = data.get("resultado")

    if not resultado:
        return jsonify({"erro": "resultado obrigatório"}), 400

    print(f"\n🚀 Novo sinal: {resultado}")

    contatos = db.collection("chats").stream()
    enviados = 0

    for c in contatos:
        numero = c.id

        msg = f"📊 NOVO SINAL DETECTADO: {resultado}x"
        enviar_whatsapp(numero, msg)

        # salvar na conversa
        db.collection("chats").document(numero).collection("mensagens").add({
            "mensagem": msg,
            "remetente": "bot",
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        enviados += 1

    return jsonify({"status": "ok", "enviados": enviados}), 200


# ======================================================
# PAINEL: ENVIAR MENSAGEM MANUAL
# ======================================================
@app.route('/enviar', methods=['POST'])
def enviar_manual():
    data = request.get_json()
    numero = data.get("numero")
    mensagem = data.get("mensagem")

    if not numero or not mensagem:
        return jsonify({"erro": "dados faltando"}), 400

    enviar_whatsapp(numero, mensagem)

    # salvar no histórico
    db.collection("chats").document(numero).collection("mensagens").add({
        "mensagem": mensagem,
        "remetente": "bot",
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    return jsonify({"status": "enviado"}), 200


# ======================================================
# PAINEL: LISTAR TODAS CONVERSAS
# ======================================================
@app.route('/mensagens')
def listar_mensagens():

    chats = db.collection("chats").stream()
    dados = {}

    for contato in chats:
        numero = contato.id
        mensagens = []

        msgs = db.collection("chats").document(numero).collection("mensagens")\
                .order_by("timestamp").stream()

        for m in msgs:
            mensagens.append(m.to_dict())

        dados[numero] = mensagens

    return jsonify(dados)


# =======================================
# START SERVIDOR
# =======================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
