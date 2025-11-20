from flask import Flask, request, render_template, jsonify
import requests
import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

app = Flask(__name__)

# ===========================================================
# CONFIG WHATSAPP API
# ===========================================================
WHATSAPP_TOKEN = "EAALl2GJDMpMBPZBu8NmFIjWvqIDKJh4B1QlNsmG7n557ffCdCnNeXZBg1bR2bGFWo1CNZCXL5jiYXpfPZCZC8ZBGMbWUXw7vx4HykAPZBJ4bWczUa8ZClwKrPbCZBXgkW9DMemDkIqqCVO7BFNkoxZBjQu7nLQIkCUmu17J9zG8ZA5fgRX5RaK4ORLEdcYOo7vuRH1DZCwZDZD"
PHONE_ID = "848088375057819"
VERIFY_TOKEN = "meu_token_webhook"


# ===========================================================
# FIREBASE ADMIN
# ===========================================================
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



# ===========================================================
# ROTA HOME (SEU JOGO)
# ===========================================================
@app.route('/')
def home():
    return render_template('index.html')



# ===========================================================
# ROTA PAINEL SECRETO
# ===========================================================
@app.route('/admin')
def admin():
    return render_template('painel.html')



# ===========================================================
# WEBHOOK VERIFICAÇÃO (GET)
# ===========================================================
@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200    

    return "Erro de verificação", 403



# ===========================================================
# RECEBER MENSAGENS WHATSAPP
# ===========================================================
@app.route('/webhook', methods=['POST'])
def receber_mensagem():
    data = request.get_json()

    print("\n📩 JSON RECEBIDO =====================")
    print(json.dumps(data, indent=4))

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages")

        if messages:
            msg = messages[0]
            numero = msg["from"]

            # =======================================================
            # EXTRAIR TEXTO EM QUALQUER FORMATO DA API META
            # =======================================================
            texto = None

            # formato comum
            if msg.get("type") == "text" and msg.get("text", {}).get("body"):
                texto = msg["text"]["body"]

            elif "text" in msg and "body" in msg["text"]:
                texto = msg["text"]["body"]

            # formato encapsulado
            elif "message" in msg and isinstance(msg["message"], dict):
                inner = msg["message"]
                if "body" in inner:
                    texto = inner["body"]

            # ultra fallback
            if not texto:
                texto = "(mensagem sem texto)"

            # =======================================================
            # SALVAR NO FIRESTORE
            # =======================================================
            db.collection("chats").document(numero).set({
                "numero": numero
            }, merge=True)

            db.collection("chats").document(numero).collection("mensagens").add({
                "mensagem": texto,
                "remetente": "cliente",
                "timestamp": firestore.SERVER_TIMESTAMP
            })

            print(f"📲 De: {numero} | 💬 {texto}")

            # =======================================================
            # RESPONDER AUTOMATICAMENTE
            # =======================================================
            enviar_whatsapp(numero, "Recebi sua mensagem, obrigado! 🔥")

    except Exception as e:
        print("❌ ERRO AO PROCESSAR:", e)

    return jsonify({"status": "recebido"}), 200



# ===========================================================
# FUNÇÃO ENVIAR MENSAGEM WHATSAPP
# ===========================================================
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
    print("📤 RESPOSTA WHATSAPP:", r.text)



# ===========================================================
# ROBÔ LOCAL ENVIA SINAL (AVIATOR)
# ===========================================================
@app.route('/enviar_sinal', methods=['POST'])
def enviar_sinal():
    data = request.get_json()
    resultado = data.get("resultado")

    if not resultado:
        return jsonify({"erro": "resultado obrigatório"}), 400

    print(f"\n🚀 SINAL DO ROBÔ LOCAL: {resultado}")

    contatos = db.collection("chats").stream()
    enviados = 0

    for c in contatos:
        numero = c.id

        msg = f"📊 NOVO SINAL DETECTADO: {resultado}x"
        enviar_whatsapp(numero, msg)

        db.collection("chats").document(numero).collection("mensagens").add({
            "mensagem": msg,
            "remetente": "bot",
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        enviados += 1

    return jsonify({"status": "ok", "enviados": enviados}), 200



# ===========================================================
# ENVIAR MANUAL DO PAINEL
# ===========================================================
@app.route('/enviar', methods=['POST'])
def enviar_manual():
    data = request.get_json()
    numero = data.get("numero")
    mensagem = data.get("mensagem")

    if not numero or not mensagem:
        return jsonify({"erro": "dados faltando"}), 400

    enviar_whatsapp(numero, mensagem)

    db.collection("chats").document(numero).collection("mensagens").add({
        "mensagem": mensagem,
        "remetente": "bot",
        "timestamp": firestore.SERVER_TIMESTAMP
    })

    return jsonify({"status": "enviado"}), 200



# ===========================================================
# LISTAR TODAS CONVERSAS PARA O PAINEL
# ===========================================================
@app.route('/mensagens')
def listar_mensagens():
    chats = db.collection("chats").stream()
    dados = {}

    for contato in chats:
        numero = contato.id
        mensagens = []

        msgs = db.collection("chats").document(numero).collection("mensagens") \
            .order_by("timestamp").stream()

        for m in msgs:
            mensagens.append(m.to_dict())

        dados[numero] = mensagens

    return jsonify(dados)



# ===========================================================
# START DO SERVIDOR
# ===========================================================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
