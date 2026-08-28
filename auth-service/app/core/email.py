import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

logger = logging.getLogger("auth-service.email")


def send_password_reset_email(to_email: str, token: str, user_name: str = "Usuário") -> bool:
    """
    Envia e-mail real com link de redefinição de senha via SMTP (Mailtrap).
    O link aponta sempre para a rota pública do Catálogo (porta pública),
    garantindo que o auth-service permaneça isolado na rede interna Docker.
    """
    catalogo_url = (settings.CATALOGO_URL or "http://localhost:8000").strip(' "\'').rstrip('/')
    reset_url = f"{catalogo_url}/reset-password?token={token}"
    subject = "Redefinição de Senha — Catálogo Tom Hanks"

    smtp_host = (settings.MAILTRAP_HOST or "sandbox.smtp.mailtrap.io").strip(' "\'')
    try:
        smtp_port = int(str(settings.MAILTRAP_PORT).strip(' "\''))
    except Exception:
        smtp_port = 2525

    smtp_user = (settings.MAILTRAP_USERNAME or "").strip(' "\'')
    smtp_pass = (settings.MAILTRAP_PASSWORD or "").strip(' "\'')
    from_email = (settings.MAILTRAP_FROM_EMAIL or "nao-responda@tomhanksfilmes.com").strip(' "\'')
    from_name = (settings.MAILTRAP_FROM_NAME or "Tom Hanks Filmes").strip(' "\'')

    html_content = f"""
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
      <meta charset="utf-8">
      <style>
        body {{
          font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #141414;
          color: #ffffff;
          padding: 20px;
          margin: 0;
        }}
        .card {{
          background-color: #1f1f1f;
          max-width: 520px;
          margin: 0 auto;
          padding: 32px;
          border-radius: 12px;
          border: 1px solid #333333;
          box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
        }}
        .logo {{
          font-size: 24px;
          font-weight: 700;
          color: #e50914;
          margin-bottom: 20px;
          display: flex;
          align-items: center;
          gap: 8px;
        }}
        h2 {{
          color: #ffffff;
          margin-top: 0;
          font-size: 20px;
        }}
        p {{
          color: #cccccc;
          line-height: 1.6;
          font-size: 15px;
        }}
        .btn-container {{
          text-align: center;
          margin: 30px 0;
        }}
        .btn {{
          display: inline-block;
          background-color: #e50914;
          color: #ffffff !important;
          padding: 14px 28px;
          text-decoration: none;
          border-radius: 6px;
          font-weight: 600;
          font-size: 16px;
        }}
        .link-box {{
          background-color: #141414;
          padding: 12px;
          border-radius: 6px;
          word-break: break-all;
          font-size: 12px;
          color: #e50914;
        }}
        .footer {{
          font-size: 12px;
          color: #777777;
          margin-top: 30px;
          border-top: 1px solid #2e2e2e;
          padding-top: 16px;
          line-height: 1.5;
        }}
      </style>
    </head>
    <body>
      <div class="card">
        <div class="logo">🎬 Catálogo Tom Hanks</div>
        <h2>Olá, {user_name}!</h2>
        <p>Recebemos uma solicitação para redefinir a sua senha de acesso ao <strong>Catálogo de Filmes Tom Hanks</strong>.</p>
        <p>Clique no botão abaixo para escolher uma nova senha. <strong>Atenção: este link expira em {settings.RESET_TOKEN_EXPIRE_MINUTES} minutos</strong> e só pode ser utilizado uma única vez.</p>
        
        <div class="btn-container">
          <a href="{reset_url}" target="_blank" class="btn">Redefinir Minha Senha</a>
        </div>

        <p style="font-size: 13px; color: #999999;">Caso o botão não funcione, copie e cole o endereço abaixo no seu navegador:</p>
        <div class="link-box">{reset_url}</div>

        <div class="footer">
          <p>Se você não solicitou a redefinição de senha, nenhuma ação é necessária. Sua senha atual permanecerá segura.</p>
          <p>© 2026 Catálogo de Filmes Tom Hanks — Microsserviço de Autenticação</p>
        </div>
      </div>
    </body>
    </html>
    """

    text_content = (
        f"Olá, {user_name}!\n\n"
        f"Recebemos uma solicitação para redefinir sua senha no Catálogo de Filmes Tom Hanks.\n"
        f"Acesse o link a seguir para criar uma nova senha (válido por {settings.RESET_TOKEN_EXPIRE_MINUTES} minutos):\n"
        f"{reset_url}\n\n"
        f"Se você não solicitou esta alteração, ignore este e-mail.\n"
    )

    if not smtp_user or not smtp_pass:
        print(f"[auth-service] AVISO: Mailtrap não configurado (MAILTRAP_USERNAME/PASSWORD vazios). Link gerado: {reset_url}")
        return True

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = to_email

        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, [to_email], msg.as_string())

        print(f"[auth-service] E-mail de recuperação enviado com sucesso via Mailtrap para {to_email}")
        return True
    except Exception as e:
        print(f"[auth-service] Erro ao enviar e-mail via Mailtrap para {to_email} ({smtp_host}:{smtp_port}): {str(e)}")
        raise
