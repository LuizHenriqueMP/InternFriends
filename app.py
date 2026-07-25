from flask import Flask
from models.Usuario import Usuario

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/criarUsuario')
def criarUsuario():
    usuario = Usuario('milena.jung@aluno.feliz.ifrs.edu.br', '26180915')
    return usuario.criarUsuario()