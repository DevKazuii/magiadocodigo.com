import os
from flask import Flask, render_template, request, jsonify, flash, session, redirect, url_for
import requests # Necessário para fazer requisições HTTP para o n8n

app = Flask(__name__)
# Chave secreta para mensagens flash e sessões. ESSENCIAL para usar 'session'.
app.secret_key = os.urandom(24) 

# --- Configuração do Webhook n8n ---
# Substitua por o URL do seu webhook n8n.
# É uma boa prática usar variáveis de ambiente para URLs de API.
# AGORA USANDO O URL DE PRODUÇÃO DO N8N PARA QUE ELE ESTEJA SEMPRE ATIVO
# ATENÇÃO: SUBSTITUA 'SEU_N8N_PRODUCTION_WEBHOOK_URL_AQUI' PELO URL REAL DO SEU N8N
N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "https://devkazuii.app.n8n.cloud/webhook/wek")

# --- Rota Principal ---
@app.route("/")
def index():
    # Tenta obter a resposta da IA da sessão e remove-a após a leitura
    # Isso evita que a resposta persista em recarregamentos futuros da página
    ai_response = session.pop('ai_response', None)
    
    # Renderiza a página principal, passando a resposta da IA para o template
    return render_template("index.html", ai_response=ai_response)

# --- Rota para Enviar Pergunta para o n8n ---
@app.route("/send_to_n8n", methods=["POST"])
def send_to_n8n():
    user_question = request.form.get("user_question")

    if not user_question:
        flash("Por favor, digite uma pergunta.", "warning")
        # Redireciona de volta para a página principal para exibir a mensagem flash
        return redirect(url_for('index'))

    # Dados a serem enviados para o n8n
    payload = {
        "question": user_question,
        "timestamp": request.args.get("timestamp"), # Exemplo: pode passar um timestamp
        "user_id": "usuario_anonimo_123" # Exemplo: pode passar um ID de usuário
    }

    try:
        # Adicionando logs para depuração
        print(f"Tentando enviar para o n8n com URL: {N8N_WEBHOOK_URL}")
        print(f"Payload enviado: {payload}")

        # Faz a requisição POST para o webhook do n8n
        # timeout é importante para não travar sua aplicação Flask
        response = requests.post(N8N_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status() # Lança um erro para status de resposta HTTP ruins (4xx ou 5xx)

        # Logs da resposta do n8n
        print(f"Status da resposta do n8n: {response.status_code}")
        print(f"Corpo da resposta do n8n (texto puro): {response.text}") # Log do texto puro
        
        # Tenta parsear a resposta como JSON
        try:
            n8n_response_data = response.json()
            print(f"Corpo da resposta do n8n (JSON parseado): {n8n_response_data}") # Log do JSON parseado
        except requests.exceptions.JSONDecodeError:
            print("Erro: Resposta do n8n não é um JSON válido.")
            n8n_response_data = {} # Define como dicionário vazio para evitar erros posteriores

        # --- Processa a resposta do n8n ---
        # AGORA BUSCA PELA CHAVE 'resposta' QUE O N8N ESTÁ ENVIANDO
        ai_response = n8n_response_data.get("resposta", "Nenhuma resposta da IA recebida do n8n.")
        
        # Armazena a resposta da IA na sessão para ser exibida na próxima requisição GET
        session['ai_response'] = ai_response
        
        flash("Pergunta enviada para o n8n com sucesso! Resposta da IA recebida.", "success")
        print(f"Resposta da IA armazenada na sessão: {ai_response}")

        # Redireciona de volta para a página principal para exibir a resposta da IA
        return redirect(url_for('index'))

    except requests.exceptions.Timeout:
        flash("Tempo limite excedido ao conectar com o n8n. Tente novamente.", "error")
        print("Erro: Timeout ao enviar para n8n")
        return redirect(url_for('index'))
    except requests.exceptions.RequestException as e:
        flash(f"Erro ao enviar pergunta para o n8n: {e}", "error")
        print(f"Erro de requisição: {e}")
        return redirect(url_for('index'))
    except Exception as e:
        flash(f"Ocorreu um erro inesperado: {e}", "error")
        print(f"Erro inesperado: {e}")
        return redirect(url_for('index'))


if __name__ == "__main__":
    # AVISO: Em produção, NUNCA use debug=True
    app.run(debug=True)
