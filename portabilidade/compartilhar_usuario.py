from flask import Flask, jsonify
from datetime import datetime
import mysql.connector
from db_config import db

app = Flask(__name__)

def get_db_connection():
    return mysql.connector.connect(**db)

# USO DE HTTPS PARA NÃO TER PESSOA DURANTE O CAMINHO QUE INTERCEPTE

@app.route('/portabilidade/<int:id>/<codigo_portabilidade>', methods=['GET'])
def compartilhar(id, codigo_portabilidade):
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    # Verificar se o código de portabilidade é válido e não expirou
    cursor.execute("""
        SELECT data_expiracao
        FROM portabilidade_codigos
        WHERE codigo = %s
    """, (codigo_portabilidade,))
    codigo_registro = cursor.fetchone()

    if not codigo_registro:
        conn.close()
        return jsonify({"mensagem": "Código de portabilidade inválido ou não encontrado."}), 404

    data_expiracao, = codigo_registro
    if datetime.now() > data_expiracao:
        conn.close()
        return jsonify({"mensagem": "Código de portabilidade expirado."}), 400

    # Recuperar dados do usuário
    cursor.execute("""
        SELECT nome, email, ativo
        FROM usuarios
        WHERE id = %s
    """, (id,))
    usuario = cursor.fetchone()
    conn.close()

    if usuario:
        nome, email, ativo = usuario
        return jsonify({
            "id": id,
            "nome": nome,
            "email": email,
            "ativo": ativo
        }), 200
    else:
        return jsonify({"mensagem": "Usuário não encontrado."}), 404

if __name__ == '__main__':
    app.run(port=5000) 
