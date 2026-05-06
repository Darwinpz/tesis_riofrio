from flask import render_template, Blueprint

error_bp = Blueprint('errors', __name__)

@error_bp.app_errorhandler(401)
def unauthorized(e):
    return render_template('/views/errors/401.html'), 401

@error_bp.app_errorhandler(403)
def forbidden(e):
    return render_template('/views/errors/403.html'), 403

@error_bp.app_errorhandler(404)
def not_found(e):
    return render_template('/views/errors/404.html'), 404

@error_bp.app_errorhandler(500)
def internal_error(e):
    return render_template('/views/errors/500.html'), 500