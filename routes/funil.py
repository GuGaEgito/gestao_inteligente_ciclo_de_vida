from flask import Blueprint, render_template
from flask_login import login_required

funil_bp = Blueprint('funil', __name__)


@funil_bp.route('/funil')
@login_required
def index():
    return render_template('funil.html')