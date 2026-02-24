from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from datetime import datetime

db = SQLAlchemy()
bcrypt = Bcrypt()

# ──────────────────────────────────────────────
# Níveis de acesso disponíveis no sistema
# ──────────────────────────────────────────────
ROLES = {
    'admin':    {'label': 'Administrador', 'nivel': 3},
    'gerente':  {'label': 'Gerente',       'nivel': 2},
    'analista': {'label': 'Analista',      'nivel': 1},
}


class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'

    id         = db.Column(db.Integer, primary_key=True)
    nome       = db.Column(db.String(100), nullable=False)
    email      = db.Column(db.String(150), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    role       = db.Column(db.String(20), nullable=False, default='analista')
    ativo      = db.Column(db.Boolean, default=True)
    criado_em  = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_login = db.Column(db.DateTime, nullable=True)

    def set_senha(self, senha):
        self.senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')

    def checar_senha(self, senha):
        return bcrypt.check_password_hash(self.senha_hash, senha)

    @property
    def role_label(self):
        return ROLES.get(self.role, {}).get('label', self.role)

    @property
    def nivel(self):
        return ROLES.get(self.role, {}).get('nivel', 0)

    def pode(self, role_minimo):
        """Verifica se o usuário tem nível >= ao papel exigido."""
        nivel_minimo = ROLES.get(role_minimo, {}).get('nivel', 99)
        return self.nivel >= nivel_minimo

    def __repr__(self):
        return f'<Usuario {self.email} [{self.role}]>'
