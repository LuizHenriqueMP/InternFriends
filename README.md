# Quadro de Comentários Anônimos

MVP em Flask com API REST, MySQL, JWT, verificação de e-mail, recuperação de senha, um comentário por dia, curtidas/descurtidas e exclusão lógica.

## Requisitos

- Python 3.11+
- MySQL 8+ ou Docker

## Inicialização rápida

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate       # Linux/macOS
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
docker compose up -d mysql
flask --app run.py db upgrade
flask --app run.py run --debug
```

Abra `http://127.0.0.1:5000`.

## Primeira migração

O projeto já inclui uma migração inicial. Para mudanças futuras:

```bash
flask --app run.py db migrate -m "descricao"
flask --app run.py db upgrade
```

## E-mail local

Com `MAIL_BACKEND=console`, os links de verificação e recuperação aparecem no terminal do Flask. Para usar Amazon SES:

```env
MAIL_BACKEND=ses
MAIL_FROM=no-reply@seudominio.com
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

O remetente precisa estar autorizado no SES. Em sandbox, os destinatários também podem precisar estar verificados.

## Fluxo de teste

1. Cadastre um e-mail pertencente a `ALLOWED_EMAIL_DOMAINS`.
2. Copie do terminal o link `/api/auth/verify-email?token=...` e abra no navegador.
3. Faça login.
4. Publique um comentário.
5. Curta ou descurta comentários.

## Endpoints principais

- `POST /api/auth/register`
- `GET /api/auth/verify-email?token=...`
- `POST /api/auth/login`
- `POST /api/auth/forgot-password`
- `POST /api/auth/reset-password`
- `DELETE /api/auth/account`
- `GET /api/comments`
- `POST /api/comments`
- `DELETE /api/comments/{id}`
- `PUT /api/comments/{id}/vote`

## Testes

```bash
pytest -q
```

Os testes usam SQLite em memória apenas para velocidade e isolamento; a aplicação local usa MySQL conforme `DATABASE_URL`.

## Decisões implementadas

- Comentários são anônimos na API, mas ligados internamente ao autor.
- Excluir conta remove e-mail e senha, mantendo os comentários.
- Excluir comentário apaga seu conteúdo e registra `deleted_at`.
- Apagar o comentário não libera uma nova publicação no mesmo dia.
- Um voto repetido com o mesmo valor remove o voto; valor oposto troca o voto.
