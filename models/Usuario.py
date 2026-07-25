import mysql.connector
import bcrypt

class Usuario:

    db = mysql.connector.connect(
        host = 'localhost',
        user = 'root',
        password = '',
        database= 'interndb'
    )

    cursor = db.cursor()

    id = 0

    def __init__(self, email, senha):
        self.email = email
        self.senha = senha

    def criarUsuario(self):
        sql = 'INSERT INTO usuarios (email, senha) VALUES (%s, %s)'
        val = (self.email, bcrypt.hashpw(self.senha.encode('utf-8'), bcrypt.gensalt()))
        self.cursor.execute(sql, val)

        self.db.commit()
        return 'Conta criada!'

    def autenticarSenha(self):
        sql = 'SELECT senha FROM usuarios WHERE id = %s'
        id = (self.id)

        self.cursor.execute(sql, id)
        result = self.cursor.fetchone()

        if bcrypt.checkpw(self.senha, result):
            print("Password match!")
        else:
            print("Incorrect password.")