from flask import render_template, request, redirect, url_for, Blueprint, flash
from services.serviceService import ServiceService
from utils.authDecorator import role_required

service_bp = Blueprint('services', __name__, url_prefix='/services')

@service_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    services = ServiceService.get_all().get("services", [])
    return render_template('/views/services/list.html', services=services)

@service_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin')
def create():
    if request.method == 'GET':
        return render_template('/views/services/form.html', action='create', service=None)
    result = ServiceService.create(request.form.to_dict())
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('services.index'))
    flash(result["message"], 'danger')
    return render_template('/views/services/form.html', action='create', service=None)

@service_bp.route('/<service_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(service_id):
    result = ServiceService.get_by_id(service_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('services.index'))
    service = result["service"]
    if request.method == 'GET':
        return render_template('/views/services/form.html', action='edit', service=service)
    result = ServiceService.update(service_id, request.form.to_dict())
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('services.index'))
    flash(result["message"], 'danger')
    return render_template('/views/services/form.html', action='edit', service=service)

@service_bp.route('/<service_id>/delete', methods=['POST'])
@role_required('admin')
def delete(service_id):
    result = ServiceService.delete(service_id)
    if result["success"]:
        flash(result["message"], 'success')
    else:
        flash(result["message"], 'danger')
    return redirect(url_for('services.index'))
