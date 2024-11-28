@app.route('/consentimento', methods=['POST'])
def cadastrar_consentimento():
    data = request.json
    versao = data['versao']
    termo = data['termo']
    obrigatorio = data['obrigatorio']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO consentimentos (versao, termo, obrigatorio) VALUES (%s, %s, %s)",
        (versao, termo, obrigatorio)
    )
    conn.commit()
    conn.close()
    
    # Notificar serviço externo (simulado)
    # Aqui, uma requisição pode ser enviada a um serviço para notificar o usuário do novo termo
    return jsonify({"mensagem": "Termo de consentimento cadastrado"}), 201

# Rota para Confirmar ou Recusar Consentimento
@app.route('/usuario/<int:usuario_id>/consentimento/<int:consentimento_id>', methods=['POST'])
def confirmar_consentimento(usuario_id, consentimento_id):
    data = request.json
    aceito = data['aceito']
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Verificar se o termo é obrigatório
    cursor.execute("SELECT obrigatorio FROM consentimentos WHERE id = %s", (consentimento_id,))
    termo = cursor.fetchone()
    
    if not termo:
        return jsonify({"erro": "Termo de consentimento não encontrado"}), 404
    
    # Registrar a aceitação ou recusa do usuário
    cursor.execute(
        "INSERT INTO consentimento_usuarios (usuario_id, consentimento_id, aceito) VALUES (%s, %s, %s)",
        (usuario_id, consentimento_id, aceito)
    )
    conn.commit()
    
    # Se o termo é obrigatório e o usuário recusou, desativá-lo
    if termo['obrigatorio'] and not aceito:
        cursor.execute("UPDATE usuarios SET ativo = FALSE WHERE id = %s", (usuario_id,))
        conn.commit()
        mensagem = "Usuário desativado devido à recusa do termo obrigatório"
    else:
        mensagem = "Consentimento atualizado com sucesso"
    
    conn.close()
    return jsonify({"mensagem": mensagem}), 200

# Rota para Notificação de um Novo Termo ao Usuário
@app.route('/notificar_usuario_novo_termo/<int:usuario_id>', methods=['GET'])
def notificar_usuario_novo_termo(usuario_id):
    # Esta rota simula a notificação de um serviço externo ao usuário para um novo termo obrigatório
    return jsonify({"mensagem": f"Usuário {usuario_id} notificado sobre o novo termo de consentimento"}), 200

# Rota para Consultar o Status do Usuário
@app.route('/usuario/<int:id>', methods=['GET'])
def consultar_status_usuario(id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM usuarios WHERE id = %s", (id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return jsonify(user)
    else:
        return jsonify({"erro": "Usuário não encontrado"}), 404

# Rota para Recuperar Consentimentos de um Usuário
@app.route('/usuario/<int:usuario_id>/consentimentos', methods=['GET'])
def listar_consentimentos(usuario_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        "SELECT c.termo, cu.aceito FROM consentimentos c LEFT JOIN consentimento_usuarios cu ON c.id = cu.consentimento_id WHERE cu.usuario_id = %s",
        (usuario_id,)
    )
    consentimentos = cursor.fetchall()
    conn.close()

    return jsonify(consentimentos), 200

# Rota para Atualizar Termos e Criar Histórico
@app.route('/consentimento/<int:consentimento_id>', methods=['PUT'])
def atualizar_termo(consentimento_id):
    data = request.json
    novo_termo = data.get('termo')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Criar histórico (se necessário)
    cursor.execute(
        "INSERT INTO consentimentos (versao, termo, obrigatorio) SELECT versao + 1, termo, obrigatorio FROM consentimentos WHERE id = %s",
        (consentimento_id,)
    )
    if novo_termo:
        cursor.execute("UPDATE consentimentos SET termo = %s WHERE id = %s", (novo_termo, consentimento_id))

    conn.commit()
    conn.close()

    return jsonify({"mensagem": "Termo atualizado com sucesso"}), 200