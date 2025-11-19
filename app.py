from flask import Flask, request, render_template, jsonify
import requests

app = Flask(__name__)

# ==========================
# CONFIG WHATSAPP API
# ==========================
WHATSAPP_TOKEN = "EAALl2GJDMpMBPZCrN3mf5EbxTnZBJyz0ReWo7oqv5KrvhPE6oCtJYFG4B9cALDiZCXECZB54oEDGKheZAcruRpMB1QhSIvbKytiMO1aZCCY55ls2H4Rf1DXrAgNSeLnueewrLFe3rEn015mTOt3lcIZCgrcdQeVqSYt7oiaIpk8WWL9anyxfKNWLiRRqcUoJos1iNcMOSwsrHGs87wQ1Sn7gNH9xfqgrsiunJrqkgfE"
PHONE_ID = "848088375057819"
VERIFY_TOKEN = "meu_token_webhook"

# ==========================
# HOME
# ==========================
@app.route('/')
def home():
    return render_template('index.html')


# ==========================
# VERIFICAÇÃO DO WEBHOOK (GET)
# ==========================
@app.route('/webhook', methods=['GET'])
def verificar_webhook():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200

    return "Erro de verificação", 403


# ==========================
# RECEBER MENSAGENS (POST)
# ==========================
@app.route('/webhook', methods=['POST'])
def receber_mensagem():
    data = request.get_json()

    print("\n📩 MENSAGEM RECEBIDA ==================")
    print(data)

    try:
        entry = data["entry"][0]["changes"][0]["value"]
        messages = entry.get("messages")

        if messages:
            msg = messages[0]
            numero = msg["from"]

            if "text" in msg:
                texto = msg["text"]["body"]
                print(f"📲 De: {numero}")
                print(f"💬 Texto: {texto}")

                # Responder automaticamente
                enviar_whatsapp(numero, "Recebi sua mensagem, obrigado! 🔥")

    except Exception as e:
        print("❌ ERRO ao processar:", e)

    return jsonify({"status": "recebido"}), 200


# ==========================
# FUNÇÃO PARA ENVIAR MENSAGENS
# ==========================
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


# ==========================
# START
# ==========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
