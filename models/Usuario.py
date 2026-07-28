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

    __id = 0

    def __init__(self, email, senha):
        self.__email = email
        self.__senha = senha

    def get_id(self):
        return self.__id

    def set_id(self, id):
        self.__id = id

    def get_email(self):
        return self.__email

    def set_email(self, email):
        self.__email = email

    def get_senha(self):
        return self.__senha

    def set_senha(self, senha):
        self.__senha = senha

    def achar_id(self):
        sql = 'SELECT id FROM usuarios WHERE email = %s'
        val = (self.__email,)
        self.cursor.execute(sql, val)

        return self.cursor.fetchone()

    @staticmethod
    def achar_usuario_por_id(self, id):
        sql = 'SELECT * FROM usuarios WHERE id = %s'
        val = (id,)
        self.cursor.execute(sql, val)

        resultado = self.cursor.fetchall()[0]
        email = resultado[1]
        senha = resultado[2]

        usuario = Usuario(email, senha)
        return usuario
        

    def criarUsuario(self):
        sql = 'INSERT INTO usuarios (email, senha) VALUES (%s, %s)'
        val = (self.__email, bcrypt.hashpw(self.__senha.encode('utf-8'), bcrypt.gensalt()))
        self.cursor.execute(sql, val)

        self.db.commit()
        return 'Usuário criado!'

    @staticmethod
    def deletar_usuario(self, id):
        sql = 'DELETE FROM usuarios WHERE id = %s'
        val = (id,)
        self.cursor.execute(sql, val)

        self.db.commit()
        return 'Usuário excluído.'

    def atualizar_usuario(self, id):
        sql = 'UPDATE usuarios SET email = %s, senha = %s WHERE id = %s'
        val = (self.__email, bcrypt.hashpw(self.__senha.encode('utf-8'), bcrypt.gensalt()), id)
        self.cursor.execute(sql, val)

        self.db.commit()
        return 'Dados atualizados.'
    
    def autenticar_senha(self):
        sql = 'SELECT senha FROM usuarios WHERE id = %s'
        val = (self.__id,)

        self.cursor.execute(sql, val)
        result = self.cursor.fetchone()

        if bcrypt.checkpw(bcrypt.hashpw(self.__senha.encode('utf-8'), bcrypt.gensalt()), result):
            return "Senha correta!"
        else:
            return "Senha incorreta."