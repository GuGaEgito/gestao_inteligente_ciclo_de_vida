from flask import Blueprint, render_template
from flask_login import login_required

ideias_bp = Blueprint('ideias', __name__)


@ideias_bp.route('/ideias')
@login_required
def index():
    return render_template('ideias.html')