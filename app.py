from flask import Flask, jsonify, request
from flask_cors import CORS
from usuario.usuarios_crud import (
    criar_usuario,
    listar_usuarios,
    obter_usuario,
    atualizar_usuario,
    excluir_usuario,
    login
)

from portabilidade.compartilhar_usuario import compartilhar

import mysql.connector
from db_config import db
def get_db_connection():
    return mysql.connector.connect(**db)

from db_config import db_historico_exclusao
def get_db_connection_exclusao():
    return mysql.connector.connect(**db_historico_exclusao)

app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})

# ======================================== CRUD USUARIOS =====================================================================

# tem que ter tela o crud de usuario

@app.route('/usuario/criar', methods=['POST'])
def route_criar_usuario():
    return criar_usuario()

@app.route('/usuarios', methods=['GET'])
def route_listar_usuarios():
    return listar_usuarios()

@app.route('/usuario/<int:id>', methods=['GET'])
def route_obter_usuario(id):
    return obter_usuario(id)

@app.route("/usuario/<int:id>", methods=["PUT"])  # Altere de POST para PUT
def route_atualizar_usuario(id):
    return atualizar_usuario(id)

@app.route('/usuario/<int:id>', methods=['DELETE'])
def route_excluir_usuario(id):
    return excluir_usuario(id)

# =========================================== Portabilidade ==============================================================

# precisa fazer uma api que vai ter como consumir o endpoint pra garantir o dado chegar certo

@app.route('/portabilidade/<int:id>/<string:codigo>', methods=['GET'])
def route_obter_portabilidade(id, codigo):
    return compartilhar(id, codigo)

@app.route("/login", methods=["POST"])
def login():
    try:
        # Log de dados recebidos
        data = request.json
        print("Dados recebidos no login:", data)

        email = data.get('email')
        senha = data.get('senha')

        if not email or not senha:
            return jsonify({"mensagem": "Email e senha são obrigatórios"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        conn_exclusao = get_db_connection_exclusao()
        cursor_exclusao = conn_exclusao.cursor()

        # Verifica se o usuário existe
        cursor.execute(
            "SELECT id, nome, email FROM usuarios WHERE email = %s AND senha = %s",
            (email, senha)
        )
        usuario = cursor.fetchone()

        if not usuario:
            print("Email ou senha incorretos.")
            return jsonify({"mensagem": "Email ou senha incorretos"}), 401

        id, nome, email = usuario  # Desempacotamento corrigido

        # Verifica se o usuário está no histórico de exclusão
        cursor_exclusao.execute(
            "SELECT usuario_id FROM historico_exclusao WHERE usuario_id = %s",
            (id,)
        )
        historico = cursor_exclusao.fetchone()

        if historico:
            print("Usuário no histórico de exclusão, bloqueando acesso...")
            cursor.execute(
                "UPDATE usuarios SET nome = NULL, email = NULL, senha = NULL WHERE id = %s",
                (id,)
            )
            conn.commit()
            return jsonify({"mensagem": "Usuário bloqueado e não pode acessar o sistema."}), 403

        # Verifica se há um novo termo que o usuário precisa autorizar
        cursor.execute(
            "SELECT id FROM termos WHERE atual = 1"
        )
        termo_atual = cursor.fetchone()

        if termo_atual:
            termo_id = termo_atual[0]

            # Verifica se o usuário já deu consentimento para o termo atual
            cursor.execute(
                "SELECT 1 FROM usuarios_consentimentos WHERE usuario_id = %s AND item_termo_id IN "
                "(SELECT id FROM itens_termo WHERE termo_id = %s) AND autorizado = 1",
                (id, termo_id)
            )
            consentimento = cursor.fetchone()

            if not consentimento:
                # Caso o usuário não tenha autorizado o novo termo, retorna todos os itens do termo
                cursor.execute(
                    "SELECT item_numero, mensagem FROM itens_termo WHERE termo_id = %s",  # Não filtra mais por obrigatoriedade
                    (termo_id,)
                )
                termos_mensagem = cursor.fetchall()

                return jsonify({
                    "id": id,
                    "mensagem": "Novo termo de consentimento. Por favor, aceite os novos termos para continuar usando o sistema.",
                    "termo_id": termo_id,
                    "itens_termo": [
                        {"item_numero": item[0], "mensagem": item[1]} for item in termos_mensagem
                    ]
                }), 200

        # Resposta de sucesso
        return jsonify({
            "id": id,
            "nome": nome,
            "email": email,
            "mensagem": "Login realizado com sucesso!"
        }), 200

    except Exception as e:
        print("Erro no login:", str(e))
        return jsonify({"mensagem": "Erro ao realizar login", "erro": str(e)}), 500
    finally:
        conn.close()
        conn_exclusao.close()

# =========================================== Consentimento ==============================================================

# Ao se cadastrar deve aceitar o inicial similar aquela bolinha de clicar que sempre tem, 
# depois ao cadastrar um novo termo pode ser obrigatorio, opcional ou ter tanto obrigatorio quanto opcional, 
# fazendo um "pop up" na tela do usuario que não escolheu uma opção ainda

@app.route("/cadastrar_termo", methods=["POST"])
def cadastrar_termo():
    data = request.json
    
    if 'versão' not in data or 'termo' not in data:
        return jsonify({"error": "Formato de JSON inválido, 'versão' e 'termo' são obrigatórios."}), 400

    versao = data['versão']
    termo_itens = data['termo']

    # Conectar ao banco de dados
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 1. Desmarcar todos os termos anteriores como 'atual' = false
        cursor.execute(
            "UPDATE termos SET atual = false"
        )
        conn.commit()

        # 2. Inserir o novo termo na tabela 'termos' com 'atual' = true
        cursor.execute(
            "INSERT INTO termos (versao, atual) VALUES (%s, true)",
            (versao,)
        )
        conn.commit()

        # Obter o ID do termo recém inserido
        termo_id = cursor.lastrowid

        # 3. Inserir os itens do termo na tabela 'itens_termo'
        for item in termo_itens:
            item_numero = item['item']
            obrigatorio = item['obrigatorio']
            mensagem = item['mensagem']

            cursor.execute(
                "INSERT INTO itens_termo (termo_id, item_numero, obrigatorio, mensagem) VALUES (%s, %s, %s, %s)",
                (termo_id, item_numero, obrigatorio, mensagem)
            )
        
        conn.commit()

        # Fechar a conexão com o banco de dados
        conn.close()

        # Retornar a resposta com o ID do termo e os itens inseridos
        return jsonify({"message": "Termo e itens cadastrados com sucesso!", "termo_id": termo_id}), 200

    except Exception as e:
        # Se ocorrer erro, desfaz as alterações no banco
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        # Se ocorrer erro, desfaz as alterações no banco
        conn.rollback()
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route("/termos", methods=["GET"])
def obter_termo_ativo():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Obter o termo ativo atual
        cursor.execute("SELECT id, versao FROM termos WHERE atual = true LIMIT 1")
        termo = cursor.fetchone()

        if not termo:
            return jsonify({"error": "Nenhum termo ativo encontrado."}), 404

        termo_id = termo['id']

        # Obter os itens associados ao termo ativo
        cursor.execute("""
            SELECT id AS item_termo_id, item_numero, obrigatorio, mensagem
            FROM itens_termo
            WHERE termo_id = %s
        """, (termo_id,))
        itens = cursor.fetchall()

        # Construir o JSON do termo ativo
        termo_json = {
            "id": termo["id"],
            "versão": termo["versao"],
            "termo": [
                {
                    "item": item["item_numero"],
                    "obrigatorio": item["obrigatorio"],
                    "mensagem": item["mensagem"]
                }
                for item in itens
            ]
        }

        return jsonify(termo_json), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

@app.route("/termos/update/<id>", methods=["POST"])
def atualizar_termos_usuario(id):
    data = request.json

    if not data or 'decisoes' not in data:
        return jsonify({"error": "Formato de JSON inválido, 'decisoes' é obrigatório."}), 400

    decisoes = data['decisoes']  # Lista de objetos com item_numero e autorizado

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Obter o termo atual
        cursor.execute("SELECT id FROM termos WHERE atual = TRUE LIMIT 1")
        termo = cursor.fetchone()

        if not termo:
            return jsonify({"error": "Nenhum termo ativo encontrado."}), 404

        termo_id = termo[0]

        # Obter todos os itens do termo atual
        cursor.execute("SELECT item_numero, id FROM itens_termo WHERE termo_id = %s", (termo_id,))
        itens_termo_mapeados = {row[0]: row[1] for row in cursor.fetchall()}  # Mapeia item_numero -> item_id

        for decisao in decisoes:
            item_numero = decisao.get('item_numero')  # Campo 'item_numero'
            autorizado = decisao.get('autorizado')

            if item_numero is None or autorizado is None:
                return jsonify({"error": "Cada decisão deve conter 'item_numero' e 'autorizado'."}), 400

            # Mapear item_numero para o ID real do item_termo
            item_termo_id = itens_termo_mapeados.get(item_numero)

            if not item_termo_id:
                return jsonify({
                    "error": f"O item_numero {item_numero} não pertence ao termo atual.",
                    "itens_termo_validos": list(itens_termo_mapeados.keys()),
                    "termo_id": termo_id
                }), 400

            # Verificar decisão atual na tabela
            cursor.execute("""
                SELECT autorizado
                FROM usuarios_consentimentos
                WHERE usuario_id = %s AND item_termo_id = %s AND decisao_atual = 1
            """, (id, item_termo_id))
            resultado = cursor.fetchone()

            if resultado is None or resultado[0] != autorizado:
                # Atualizar decisão antiga para `decisao_atual = 0`
                cursor.execute("""
                    UPDATE usuarios_consentimentos
                    SET decisao_atual = 0
                    WHERE usuario_id = %s AND item_termo_id = %s AND decisao_atual = 1
                """, (id, item_termo_id))

                # Inserir nova decisão como `decisao_atual = 1`
                cursor.execute("""
                    INSERT INTO usuarios_consentimentos (usuario_id, item_termo_id, decisao_atual, autorizado)
                    VALUES (%s, %s, 1, %s)
                """, (id, item_termo_id, autorizado))

        conn.commit()
        return jsonify({"mensagem": "Decisões atualizadas com sucesso!"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()

@app.route("/autorizacao_usuario/<id>", methods=["POST"])
def salvar_autorizacoes_usuario(id):
    data = request.json

    if not data or 'decisoes' not in data:
        return jsonify({"error": "Formato de JSON inválido, 'decisoes' é obrigatório."}), 400

    decisoes = data['decisoes']  # Lista de objetos com item_numero e autorizado

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Obter o termo atual
        cursor.execute("SELECT id FROM termos WHERE atual = TRUE LIMIT 1")
        termo = cursor.fetchone()

        if not termo:
            return jsonify({"error": "Nenhum termo ativo encontrado."}), 404

        termo_id = termo[0]

        # Obter todos os itens do termo atual
        cursor.execute("SELECT item_numero, id FROM itens_termo WHERE termo_id = %s", (termo_id,))
        itens_termo_mapeados = {row[0]: row[1] for row in cursor.fetchall()}  # Mapeia item_numero -> item_id

        # Validar e processar decisões
        for decisao in decisoes:
            item_numero = decisao.get('item_numero')  # Campo 'item_numero'
            autorizado = decisao.get('autorizado')

            if item_numero is None or autorizado is None:
                return jsonify({"error": "Cada decisão deve conter 'item_numero' e 'autorizado'."}), 400

            # Mapear item_numero para o ID real do item_termo
            item_termo_id = itens_termo_mapeados.get(item_numero)

            if not item_termo_id:
                return jsonify({
                    "error": f"O item_numero {item_numero} não pertence ao termo atual.",
                    "itens_termo_validos": list(itens_termo_mapeados.keys()),  # Lista os itens válidos
                    "termo_id": termo_id
                }), 400

            # Atualizar todas as decisões anteriores para `decisao_atual = 0`
            cursor.execute(""" 
                UPDATE usuarios_consentimentos 
                SET decisao_atual = 0 
                WHERE usuario_id = %s AND item_termo_id = %s 
            """, (id, item_termo_id))

            # Inserir nova decisão como `decisao_atual = 1`
            cursor.execute("""
                INSERT INTO usuarios_consentimentos (usuario_id, item_termo_id, decisao_atual, autorizado)
                VALUES (%s, %s, 1, %s)
            """, (id, item_termo_id, autorizado))

        conn.commit()
        return jsonify({"mensagem": "Decisões salvas com sucesso!"}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route("/termo_usuario/<id>", methods=["GET"])
def obter_termos_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Obter o termo ativo
        cursor.execute("SELECT id, versao, data_cadastro FROM termos WHERE atual = TRUE LIMIT 1")
        termo = cursor.fetchone()

        if not termo:
            return jsonify({"error": "Nenhum termo ativo encontrado."}), 404

        termo_id, versao, data_cadastro = termo

        # Obter os itens do termo ativo com as decisões do usuário
        cursor.execute("""
            SELECT it.item_numero, it.obrigatorio, it.mensagem, uc.autorizado, uc.autorizado_em
            FROM itens_termo it
            JOIN usuarios_consentimentos uc ON it.id = uc.item_termo_id
            WHERE uc.usuario_id = %s AND uc.decisao_atual = 1 AND it.termo_id = %s
        """, (id, termo_id))

        itens_usuario = cursor.fetchall()

        if not itens_usuario:
            return jsonify({"error": "Nenhuma decisão encontrada para o usuário no termo atual."}), 404

        # Construir a resposta
        resposta = {
            "termo": {
                "id": termo_id,
                "versao": versao,
                "data_cadastro": data_cadastro,
                "itens": [
                    {
                        "item_numero": item[0],
                        "obrigatorio": item[1],
                        "mensagem": item[2],
                        "autorizado": item[3],
                        "autorizado_em": item[4]
                    }
                    for item in itens_usuario
                ]
            }
        }

        return jsonify(resposta), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        conn.close()


# Inicializa o servidor Flask
if __name__ == '__main__':
    app.run(debug=True)
