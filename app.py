from flask import Flask, render_template_string
import firebase_admin
from firebase_admin import credentials, firestore
import os, json

app = Flask(__name__)

# 🔥 Conexão Firebase
firebase_key = os.environ.get("FIREBASE_KEY")
cred = credentials.Certificate(json.loads(firebase_key))
firebase_admin.initialize_app(cred)
db = firestore.client()

# HTML simples
HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Painel de Resultados</title>
<style>
  body { background:#0e0e0e; color:white; font-family:Arial; text-align:center; }
  h1 { color:#ff004c; }
  table { margin:auto; border-collapse:collapse; width:80%; background:#1a1a1a; }
  th,td { border:1px solid #333; padding:8px; }
  tr:nth-child(even){ background:#222; }
</style>
</head>
<body>
  <h1>📊 Painel de Resultados</h1>
  <h2>Último resultado: {{ultimo}}</h2>
  <table>
    <tr><th>Rodada</th><th>Resultado</th><th>Hora</th></tr>
    {% for h in historico %}
      <tr><td>{{h.rodada}}</td><td>{{h.resultado}}</td><td>{{h.hora}}</td></tr>
    {% endfor %}
  </table>
</body>
</html>
"""

@app.route('/')
def index():
    ultimo_doc = db.collection("resultados").document("ultimo").get()
    ultimo = ultimo_doc.to_dict().get("valor", "—") if ultimo_doc.exists else "—"

    historico_docs = db.collection("historico").order_by("timestamp", direction="DESCENDING").limit(15).stream()
    historico = [{
        "rodada": h.to_dict().get("rodada"),
        "resultado": h.to_dict().get("resultado"),
        "hora": h.to_dict().get("timestamp").strftime("%H:%M:%S") if h.to_dict().get("timestamp") else ""
    } for h in historico_docs]

    return render_template_string(HTML, ultimo=ultimo, historico=historico)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
