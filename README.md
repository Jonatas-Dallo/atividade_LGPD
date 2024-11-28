# Atividade LGPD (Lei Geral de Proteção de Dados)

## Para rodar o projeto:

- Dar pip install -r requirements.tx e depois executar app.py

- dentro da pasta front_basico rodar npm install e depois npm start

Observação: Rodar py portabilidade_simulacao.py para testar o codigo necessário para terceiros terem os dados do usario compartilhado

Observação: Rodar py notificacao_emergencia.py para testar o código de alerta de emergencia, caso o sistema ou dados tenham sido comprometidos, precisando avisar os usuarios que deu problema.

# Banco Script para usar no Mysql Workbench

```CREATE DATABASE IF NOT EXISTS lgpd_db;
USE lgpd_db;

CREATE TABLE usuarios (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100),
    email VARCHAR(100),
    senha VARCHAR(100)
);

CREATE TABLE historico (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT,
    acao VARCHAR(100),
    data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE portabilidade_codigos (
    id SERIAL PRIMARY KEY,
    codigo VARCHAR(255) UNIQUE NOT NULL,
    data_expiracao TIMESTAMP NOT NULL,
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE termos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    versao VARCHAR(10) NOT NULL UNIQUE,
    atual BOOLEAN DEFAULT true,
    data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE itens_termo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    termo_id INT NOT NULL, -- Relaciona ao termo
    item_numero INT NOT NULL, -- Número do item dentro do termo
    obrigatorio BOOLEAN NOT NULL,
    mensagem TEXT NOT NULL,
    FOREIGN KEY (termo_id) REFERENCES termos(id),
    UNIQUE (termo_id, item_numero)
);

CREATE TABLE usuarios_consentimentos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    item_termo_id INT NOT NULL, -- Relaciona ao item do termo
    decisao_atual boolean NOT NULL,
    autorizado BOOLEAN NOT NULL,
    autorizado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (item_termo_id) REFERENCES itens_termo(id)
);

CREATE DATABASE IF NOT EXISTS historico_exclusao;
USE historico_exclusao;

CREATE TABLE historico_exclusao (
    id INT AUTO_INCREMENT PRIMARY KEY,
    usuario_id INT NOT NULL,
    data_exclusao DATETIME DEFAULT CURRENT_TIMESTAMP
);

USE lgpd_db;


