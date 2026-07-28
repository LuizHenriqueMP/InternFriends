from flask import Flask
from models.Usuario import Usuario

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/criarUsuario')
def criarUsuario(email, senha):
    usuario = Usuario(email, senha)
    return usuario.criarUsuario()

@app.route('/acharUsuario')
def acharUsuario():
    return Usuario.achar_usuario_por_id(Usuario, 2)