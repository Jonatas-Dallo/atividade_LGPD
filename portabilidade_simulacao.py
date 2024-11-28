from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

API_KEY = "sakaue"  

# criptografar e chave assimetrica

# USO DE HTTPS PARA NÃO TER PESSOA DURANTE O CAMINHO QUE INTERCEPTE

PORTABILIDADE_URL = "http://localhost:5000/portabilidade"

@app.route('/api/portabilidade/<int:id>/<codigo_portabilidade>', methods=['GET'])
def acessar_portabilidade(id, codigo_portabilidade):
    api_key = request.headers.get('X-API-KEY')
    if api_key != API_KEY:
        return jsonify({"mensagem": "Chave de API inválida."}), 403

    try:
        response = requests.get(f"{PORTABILIDADE_URL}/{id}/{codigo_portabilidade}")
        return jsonify(response.json()), response.status_code
    except requests.RequestException as e:
        return jsonify({"mensagem": "Erro ao conectar ao serviço de portabilidade.", "erro": str(e)}), 500

if __name__ == '__main__':
    app.run(port=5001) 
