import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import current_app


logger = logging.getLogger(__name__)


def send_email(to_address: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    backend = current_app.config["MAIL_BACKEND"]
    if backend == "console":
        logger.warning("E-MAIL LOCAL para=%s assunto=%s\n%s", to_address, subject, text_body)
        return

    if backend != "resend":
        raise RuntimeError("MAIL_BACKEND deve ser 'console' ou 'resend'.")

    api_key = current_app.config["RESEND_API_KEY"]
    if not api_key:
        raise RuntimeError("RESEND_API_KEY não está configurada.")

    payload = {
        "from": current_app.config["MAIL_FROM"],
        "to": [to_address],
        "subject": subject,
        "text": text_body,
    }
    if html_body:
        payload["html"] = html_body

    request = Request(
        "https://api.resend.com/emails",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            response.read()
    except HTTPError as error:
        response_body = error.read().decode("utf-8", errors="replace")
        logger.error(
            "Resend rejeitou o e-mail para=%s status=%s resposta=%s",
            to_address,
            error.code,
            response_body,
        )
        raise RuntimeError(
            f"Resend rejeitou o e-mail (HTTP {error.code}): {response_body}"
        ) from error
    except URLError as error:
        logger.error("Falha de conexão com o Resend para=%s: %s", to_address, error)
        raise RuntimeError("Não foi possível conectar ao Resend.") from error
