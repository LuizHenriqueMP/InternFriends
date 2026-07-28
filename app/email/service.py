import logging

import boto3
from flask import current_app


logger = logging.getLogger(__name__)


def send_email(to_address: str, subject: str, text_body: str, html_body: str | None = None) -> None:
    backend = current_app.config["MAIL_BACKEND"]
    if backend == "console":
        logger.warning("E-MAIL LOCAL para=%s assunto=%s\n%s", to_address, subject, text_body)
        return

    if backend != "ses":
        raise RuntimeError("MAIL_BACKEND deve ser 'console' ou 'ses'.")

    client = boto3.client("sesv2", region_name=current_app.config["AWS_REGION"])
    body = {"Text": {"Data": text_body, "Charset": "UTF-8"}}
    if html_body:
        body["Html"] = {"Data": html_body, "Charset": "UTF-8"}

    client.send_email(
        FromEmailAddress=current_app.config["MAIL_FROM"],
        Destination={"ToAddresses": [to_address]},
        Content={
            "Simple": {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body,
            }
        },
    )
