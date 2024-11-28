import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import mysql.connector
from db_config import db, db_historico_exclusao


# Configuração do SMTP (ajuste conforme necessário)
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587
EMAIL = 'nocloud76@gmail.com'  # Substitua pelo seu email
EMAIL_PASSWORD = 'fngq edxc vwsz wukl'   # Substitua pela senha do email

def get_db_connection_exclusao():
    return mysql.connector.connect(**db_historico_exclusao)

def get_db_connection():
    return mysql.connector.connect(**db)

def enviar_email(destinatario, assunto, mensagem):
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = destinatario
        msg['Subject'] = assunto

        msg.attach(MIMEText(mensagem, 'plain'))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Email enviado para {destinatario}")
    except Exception as e:
        print()

def notificar_comprometimento():
    conn_exclusao = get_db_connection_exclusao()
    cursor_exclusao = conn_exclusao.cursor()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Obter IDs dos usuários no histórico de exclusão
        cursor_exclusao.execute("SELECT usuario_id FROM historico_exclusao")
        ids_excluidos = {row[0] for row in cursor_exclusao.fetchall()}

        # Obter todos os usuários ativos, excluindo os que estão no `historico_exclusao`
        cursor.execute("SELECT id, email FROM usuarios WHERE id NOT IN (%s)", 
                       (",".join(map(str, ids_excluidos)),))
        usuarios_ativos = cursor.fetchall()

        # Mensagem de notificação
        assunto = "Notificação de Segurança - Dados Possivelmente Comprometidos"
        mensagem = (
            "Prezado(a) usuário(a),\n\n"
            "Informamos que os seus dados podem ter sido comprometidos devido a uma falha de segurança. "
            "Recomendamos que fique atento(a) a qualquer atividade incomum relacionada à sua conta e altere suas senhas.\n\n"
            "Atenciosamente,\nEquipe de Segurança."
        )

        # Enviar email para cada usuário ativo
        for _, email in usuarios_ativos:
            enviar_email(email, assunto, mensagem)

        print("Notificações enviadas com sucesso.")
    except Exception as e:
        print(f"Erro durante o processo de notificação: {e}")
    finally:
        conn_exclusao.close()
        conn.close()



if __name__ == "__main__":
    notificar_comprometimento()
