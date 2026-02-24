from flask import Flask
from flask_login import LoginManager
from models import db, bcrypt, Usuario
from datetime import datetime
import os

login_manager = LoginManager()


def create_app():
    app = Flask(__name__)

    # ── Configurações ──────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'troque-esta-chave-em-producao-2024!')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True   # segurança: JS não acessa cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

    # ── Extensões ─────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view       = 'auth.login'
    login_manager.login_message    = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'warning'

    # ── Blueprints ────────────────────────────────────────
    from routes.auth      import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.ideias    import ideias_bp
    from routes.funil     import funil_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(ideias_bp)
    app.register_blueprint(funil_bp)

    # ── Contexto global para templates ────────────────────
    @app.context_processor
    def inject_globals():
        return {'ano': datetime.utcnow().year}

    # ── Cria tabelas e usuário admin inicial ──────────────
    with app.app_context():
        db.create_all()
        _criar_admin_inicial()

    return app


@login_manager.user_loader
def load_user(user_id):
    return Usuario.query.get(int(user_id))


def _criar_admin_inicial():
    """Cria um admin padrão se não existir nenhum usuário no banco."""
    if not Usuario.query.first():
        admin = Usuario(
            nome  = 'Administrador',
            email = 'admin@empresa.com',
            role  = 'admin',
            ativo = True,
        )
        admin.set_senha('Admin@1234')
        db.session.add(admin)
        db.session.commit()
        print('[INFO] Usuário admin criado: admin@empresa.com / Admin@1234')


# ── Entry-point ───────────────────────────────────────────
if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
