from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario, ROLES
from datetime import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__)


# ── Decorator de acesso por role ──────────────────────────────────────────────
def requer_role(role_minimo):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.pode(role_minimo):
                flash('Você não tem permissão para acessar esta área.', 'danger')
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator


# ── Login ─────────────────────────────────────────────────────────────────────
@auth_bp.route('/', methods=['GET', 'POST'])
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email   = request.form.get('email', '').strip().lower()
        senha   = request.form.get('senha', '')
        lembrar = request.form.get('lembrar') == 'on'

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.checar_senha(senha):
            flash('E-mail ou senha inválidos.', 'danger')
            return render_template('login.html')

        if not usuario.ativo:
            flash('Sua conta está desativada. Contate o administrador.', 'warning')
            return render_template('login.html')

        login_user(usuario, remember=lembrar)
        usuario.ultimo_login = datetime.utcnow()
        db.session.commit()

        next_page = request.args.get('next')
        return redirect(next_page or url_for('dashboard.index'))

    return render_template('login.html')


# ── Logout ────────────────────────────────────────────────────────────────────
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Sessão encerrada com sucesso.', 'info')
    return redirect(url_for('auth.login'))


# ── Listar Usuários (admin) ───────────────────────────────────────────────────
@auth_bp.route('/usuarios')
@login_required
@requer_role('admin')
def listar_usuarios():
    usuarios = Usuario.query.order_by(Usuario.nome).all()
    return render_template('usuarios.html', usuarios=usuarios, roles=ROLES)


# ── Novo Usuário ──────────────────────────────────────────────────────────────
@auth_bp.route('/usuarios/novo', methods=['GET', 'POST'])
@login_required
@requer_role('admin')
def novo_usuario():
    if request.method == 'POST':
        nome  = request.form.get('nome', '').strip()
        email = request.form.get('email', '').strip().lower()
        senha = request.form.get('senha', '')
        role  = request.form.get('role', 'analista')

        erros = []
        if not nome:           erros.append('Nome obrigatório.')
        if not email:          erros.append('E-mail obrigatório.')
        if len(senha) < 6:     erros.append('Senha deve ter ao menos 6 caracteres.')
        if role not in ROLES:  erros.append('Papel inválido.')
        if Usuario.query.filter_by(email=email).first():
            erros.append('E-mail já cadastrado.')

        if erros:
            for e in erros:
                flash(e, 'danger')
            return render_template('usuario_form.html', roles=ROLES, action='novo')

        u = Usuario(nome=nome, email=email, role=role)
        u.set_senha(senha)
        db.session.add(u)
        db.session.commit()
        flash(f'Usuário {nome} criado com sucesso!', 'success')
        return redirect(url_for('auth.listar_usuarios'))

    return render_template('usuario_form.html', roles=ROLES, action='novo')


# ── Editar Usuário ────────────────────────────────────────────────────────────
@auth_bp.route('/usuarios/<int:uid>/editar', methods=['GET', 'POST'])
@login_required
@requer_role('admin')
def editar_usuario(uid):
    usuario = Usuario.query.get_or_404(uid)

    if request.method == 'POST':
        usuario.nome  = request.form.get('nome', '').strip()
        usuario.role  = request.form.get('role', usuario.role)
        usuario.ativo = request.form.get('ativo') == 'on'

        nova_senha = request.form.get('senha', '')
        if nova_senha:
            if len(nova_senha) < 6:
                flash('Senha deve ter ao menos 6 caracteres.', 'danger')
                return render_template('usuario_form.html', usuario=usuario,
                                       roles=ROLES, action='editar')
            usuario.set_senha(nova_senha)

        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('auth.listar_usuarios'))

    return render_template('usuario_form.html', usuario=usuario, roles=ROLES, action='editar')


# ── Excluir Usuário ───────────────────────────────────────────────────────────
@auth_bp.route('/usuarios/<int:uid>/excluir', methods=['POST'])
@login_required
@requer_role('admin')
def excluir_usuario(uid):
    if uid == current_user.id:
        flash('Você não pode excluir sua própria conta.', 'danger')
        return redirect(url_for('auth.listar_usuarios'))
    u = Usuario.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    flash(f'Usuário {u.nome} removido.', 'success')
    return redirect(url_for('auth.listar_usuarios'))


# ── Perfil ────────────────────────────────────────────────────────────────────
@auth_bp.route('/perfil', methods=['GET', 'POST'])
@login_required
def perfil():
    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha  = request.form.get('nova_senha', '')
        confirmar   = request.form.get('confirmar', '')

        if not current_user.checar_senha(senha_atual):
            flash('Senha atual incorreta.', 'danger')
        elif nova_senha != confirmar:
            flash('As senhas não coincidem.', 'danger')
        elif len(nova_senha) < 6:
            flash('Nova senha deve ter ao menos 6 caracteres.', 'danger')
        else:
            current_user.set_senha(nova_senha)
            db.session.commit()
            flash('Senha alterada com sucesso!', 'success')

    return render_template('perfil.html')