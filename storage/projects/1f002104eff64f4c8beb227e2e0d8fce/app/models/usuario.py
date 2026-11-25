from app.models.pessoa import Pessoa

class Usuario(Pessoa):
    def __init__(self, matricula, nome, email, telefone, endereco, setor, tipo):
        self.id = None
        self.matricula = matricula
        self.nome = nome
        self.email = email
        self.telefone = telefone
        self.endereco = endereco
        self.setor = setor
        self.tipo = tipo
        self.bloqueado = False

