from flask import jsonify, request
import mysql.connector
from db_config import db
from db_config import db_historico_exclusao

def get_db_connection():
    return mysql.connector.connect(**db)

def get_db_connection_exclusao():
    return mysql.connector.connect(**db_historico_exclusao)

def criar_usuario():
    data = request.json
    nome = data['nome']
    email = data['email']
    senha = data['senha']
    
    # Conectar ao banco de dados
    conn = get_db_connection()
    cursor = conn.cursor()

    # Inserir o usuário na tabela de usuários
    cursor.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (%s, %s, %s)",
        (nome, email, senha)
    )
    conn.commit()

    # Recuperar o ID do usuário recém-criado
    user_id = cursor.lastrowid

    # Fechar a conexão com o banco de dados
    conn.close()
    
    # Retornar a resposta com o ID do usuário criado
    return jsonify({"mensagem": "Usuário criado com sucesso", "id": user_id, "nome": nome, "email": email, "senha": senha}), 201

def listar_usuarios():
    conn = get_db_connection()
    cursor = conn.cursor(buffered=True)

    conn_exclusao = get_db_connection_exclusao()
    cursor_exclusao = conn_exclusao.cursor(buffered=True)

    cursor.execute("SELECT id, nome, email, senha FROM usuarios")
    usuarios = cursor.fetchall()

    lista_usuarios = []
    ids_para_atualizar = []

    for usuario in usuarios:
        id, nome, email, senha = usuario

        # Verifica se o usuário está no histórico de exclusão
        cursor_exclusao.execute("SELECT usuario_id FROM historico_exclusao WHERE usuario_id = %s", (id,))
        historico = cursor_exclusao.fetchone()

        if historico:
            # Adiciona o ID à lista de IDs para atualizar
            ids_para_atualizar.append(id)

            lista_usuarios.append({
                "id": id,
                "nome": None,
                "email": None,
                "senha": None
            })
        else:
            # Adiciona o usuário normalmente na lista
            lista_usuarios.append({
                "id": id,
                "nome": nome,
                "email": email,
                "senha": senha
            })

    # Realiza a atualização de todos os usuários marcados para anonimizar
    if ids_para_atualizar:
        cursor.executemany(
            "UPDATE usuarios SET nome = NULL, email = NULL, senha = NULL, ativo = 0 WHERE id = %s",
            [(id,) for id in ids_para_atualizar]
        )
        conn.commit()

    conn.close()
    conn_exclusao.close()
    
    return jsonify(lista_usuarios), 200

def obter_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor()

    conn_exclusao = get_db_connection_exclusao()
    cursor_exclusao = conn_exclusao.cursor()

    # Verifica se o usuário está no histórico de exclusão
    cursor_exclusao.execute("SELECT usuario_id FROM historico_exclusao WHERE usuario_id = %s", (id,))
    historico = cursor_exclusao.fetchone()  # Consome o resultado

    if historico:
        cursor.execute(
            "UPDATE usuarios SET nome = NULL, email = NULL, senha = FALSE, ativo = 0 WHERE id = %s",
            (id,)
        )
        conn.commit()  # Commit apenas na conexão principal
        
        return {
            "id": id,
            "nome": None,
            "email": None,
            "senha": None,
        }, 200

    # Busca dados do usuário
    cursor.execute("SELECT nome, email, senha FROM usuarios WHERE id = %s", (id,))
    usuario = cursor.fetchone()  # Consome o resultado

    if usuario:
        nome, email, senha = usuario
        return {
            "id": id,
            "nome": nome,
            "email": email,
            "senha": senha
        }, 200
    else:
        return {"mensagem": "Usuário não encontrado."}, 404

def atualizar_usuario(id):
    data = request.json
    nome = data.get("nome")
    email = data.get("email")
    senha = data.get("senha")
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Atualiza os dados no banco de dados, se forem passados
    if nome:
        cursor.execute("UPDATE usuarios SET nome = %s WHERE id = %s", (nome, id))
    if email:
        cursor.execute("UPDATE usuarios SET email = %s WHERE id = %s", (email, id))
    if senha:
        cursor.execute("UPDATE usuarios SET senha = %s WHERE id = %s", (senha, id))

    conn.commit()
    conn.close()
    
    return jsonify({"mensagem": "Usuário atualizado com sucesso"}), 200

def excluir_usuario(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        conn_exclusao = get_db_connection_exclusao()
        cursor_exclusao = conn_exclusao.cursor()

        # Adicionar ao histórico de exclusão
        cursor_exclusao.execute("INSERT INTO historico_exclusao (usuario_id) VALUES (%s)", (id,))

        # Atualizar os campos nome e email para NULL, e senha para FALSE
        cursor.execute("""
            UPDATE usuarios 
            SET nome = NULL, email = NULL, senha = NULL, ativo = 0
            WHERE id = %s
        """, (id,))

        # Confirmar todas as alterações
        conn.commit()
        conn_exclusao.commit()

    except Exception as e:
        # Em caso de erro, reverter alterações e retornar uma mensagem
        conn.rollback()
        conn_exclusao.rollback()
        return jsonify({"mensagem": "Erro ao excluir o usuário", "erro": str(e)}), 500

    finally:
        # Garantir que a conexão seja fechada
        if conn:
            conn.close()
        if conn_exclusao:
            conn_exclusao.close()
            
    return jsonify({"mensagem": "Usuário excluído com sucesso"}), 204

def login():
    data = request.json
    email = data.get('email')
    senha = data.get('senha')

    conn = get_db_connection()
    cursor = conn.cursor()

    print(data)

    try:
        # Busca o usuário com o email e senha fornecidos
        cursor.execute(
            "SELECT id, nome, email FROM usuarios WHERE email = %s AND senha = %s",
            (email, senha)
        )
        usuario = cursor.fetchone()

        print(usuario)

        if usuario:
            id, nome, email = usuario
            return jsonify({
                "id": id,
                "nome": nome,
                "email": email,
                "mensagem": "Login realizado com sucesso!"
            }), 200
        else:
            return jsonify({"mensagem": "Email ou senha incorretos"}), 401
    except Exception as e:
        return jsonify({"mensagem": "Erro ao realizar login", "erro": str(e)}), 500
    finally:
        conn.close()
