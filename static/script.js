const input = document.getElementById("imageInput");
const resultado = document.getElementById("resultado");
const historicoUl = document.getElementById("historico");
const ctx = document.getElementById("grafico").getContext("2d");

let historico = JSON.parse(localStorage.getItem("historico")) || [];

function atualizarHistorico() {
    historicoUl.innerHTML = "";
    historico.slice(-10).reverse().forEach(item => {
        const li = document.createElement("li");
        li.textContent = `${item.data} → ${item.valor}`;
        historicoUl.appendChild(li);
    });
    desenharGrafico();
}

function desenharGrafico() {
    const ultimos = historico.slice(-10);
    const labels = ultimos.map(h => h.data);
    const dados = ultimos.map(h => h.valor);

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: "Resultados",
                data: dados,
                borderColor: "#00c9ff",
                backgroundColor: "rgba(0,201,255,0.1)",
                fill: true,
                tension: 0.3
            }]
        },
        options: { scales: { y: { beginAtZero: true } } }
    });
}

async function enviarImagem() {
    const file = input.files[0];
    if (!file) {
        resultado.textContent = "⚠️ Selecione uma imagem.";
        return;
    }

    const formData = new FormData();
    formData.append("image", file);

    resultado.textContent = "🔄 Lendo...";
    const res = await fetch("/ocr", { method: "POST", body: formData });
    const data = await res.json();

    if (data.resultado) {
        resultado.textContent = `✅ Resultado: ${data.resultado}`;
        historico.push({ valor: data.resultado, data: new Date().toLocaleTimeString() });
        localStorage.setItem("historico", JSON.stringify(historico));
        atualizarHistorico();
    } else {
        resultado.textContent = "❌ Nenhum número detectado.";
    }
}

function limpar() {
    if (confirm("Apagar todo o histórico?")) {
        historico = [];
        localStorage.removeItem("historico");
        atualizarHistorico();
    }
}

atualizarHistorico();
