from flask import Flask
from models.Usuario import Usuario

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/criarUsuario')
def criarUsuario():
    usuario = Usuario('milena.jung@aluno.feliz.ifrs.edu.br', '1234')
    return usuario.criarUsuario()

@app.route('/acharUsuario')
def acharUsuario():
    usuario =  Usuario.achar_usuario_por_id(Usuario, 3)
    return usuario.get_email()+'\n'+usuario.get_senha()

@app.route('/deletarUsuario')
def deletarUsuario():
    return Usuario.deletar_usuario(Usuario, 5)

@app.route('/atualizarUsuario')
def atualizarUsuario():
    usuario = Usuario('milena.jung@aluno.feliz.ifrs.edu.br', '1234')
    id = usuario.achar_id()[0]
    usuario.set_email('milena.pacheco@aluno.feliz.ifrs.edu.br')

    return usuario.atualizar_usuario(id)
