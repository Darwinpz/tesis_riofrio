from flask import render_template, request, redirect, url_for, Blueprint, flash
from services.commonErrorService import CommonErrorService
from services.brandService import BrandService
from services.vehicleModelService import VehicleModelService
from utils.authDecorator import role_required, login_required

common_error_bp = Blueprint('common_errors', __name__, url_prefix='/common-errors')


def _form_data():
    brands = BrandService.get_all().get("brands", [])
    vehicle_models = VehicleModelService.get_all().get("vehicle_models", [])
    return brands, vehicle_models


@common_error_bp.route('/', methods=['GET'])
@login_required
def index():
    brand_id = request.args.get('brand_id', '').strip() or None
    vehicle_model_id = request.args.get('vehicle_model_id', '').strip() or None
    errors = CommonErrorService.get_all(brand_id, vehicle_model_id).get("errors", [])
    brands, vehicle_models = _form_data()
    brands_map = {b.id: b.name for b in brands}
    models_map = {vm.id: vm.name for vm in vehicle_models}
    return render_template('/views/common_errors/list.html',
                           errors=errors,
                           brands=brands,
                           vehicle_models=vehicle_models,
                           brands_map=brands_map,
                           models_map=models_map,
                           filter_brand=brand_id or '',
                           filter_model=vehicle_model_id or '')


@common_error_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin')
def create():
    brands, vehicle_models = _form_data()
    if request.method == 'GET':
        return render_template('/views/common_errors/form.html', action='create',
                               error=None, brands=brands, vehicle_models=vehicle_models)

    f = request.form
    result = CommonErrorService.create(
        brand_id=f.get('brand_id', '').strip(),
        vehicle_model_id=f.get('vehicle_model_id', '').strip(),
        year_from=f.get('year_from', '').strip(),
        year_to=f.get('year_to', '').strip(),
        title=f.get('title', '').strip(),
        description=f.get('description', '').strip(),
        severity=f.get('severity', 'media')
    )
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('common_errors.index'))
    flash(result["message"], 'danger')
    return render_template('/views/common_errors/form.html', action='create',
                           error=f.to_dict(), brands=brands, vehicle_models=vehicle_models)


@common_error_bp.route('/<error_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(error_id):
    brands, vehicle_models = _form_data()
    result = CommonErrorService.get_by_id(error_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('common_errors.index'))
    error = result["error"]

    if request.method == 'GET':
        return render_template('/views/common_errors/form.html', action='edit',
                               error=error, brands=brands, vehicle_models=vehicle_models)

    f = request.form
    upd = CommonErrorService.update(
        error_id=error_id,
        brand_id=f.get('brand_id', '').strip(),
        vehicle_model_id=f.get('vehicle_model_id', '').strip(),
        year_from=f.get('year_from', '').strip(),
        year_to=f.get('year_to', '').strip(),
        title=f.get('title', '').strip(),
        description=f.get('description', '').strip(),
        severity=f.get('severity', 'media')
    )
    if upd["success"]:
        flash(upd["message"], 'success')
        return redirect(url_for('common_errors.index'))
    flash(upd["message"], 'danger')
    return render_template('/views/common_errors/form.html', action='edit',
                           error=error, brands=brands, vehicle_models=vehicle_models)


@common_error_bp.route('/<error_id>/delete', methods=['POST'])
@role_required('admin')
def delete(error_id):
    result = CommonErrorService.delete(error_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('common_errors.index'))
