from flask import render_template, request, redirect, url_for, Blueprint, flash, jsonify
from services.vehicleModelService import VehicleModelService
from services.brandService import BrandService
from utils.authDecorator import role_required, login_required

vehicle_model_bp = Blueprint('vehicle_models', __name__, url_prefix='/vehicle-models')

@vehicle_model_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    result = VehicleModelService.get_all()
    brands = BrandService.get_all().get("brands", [])
    brands_map = {b.id: b.name for b in brands}
    return render_template('/views/vehicle_models/list.html',
                           vehicle_models=result.get("vehicle_models", []),
                           brands_map=brands_map)

@vehicle_model_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin')
def create():
    brands = BrandService.get_all().get("brands", [])
    if request.method == 'GET':
        return render_template('/views/vehicle_models/form.html', action='create',
                               vehicle_model=None, brands=brands)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    brand_id = request.form.get('brand_id', '').strip()
    result = VehicleModelService.create(name, description, brand_id)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('vehicle_models.index'))
    flash(result["message"], 'danger')
    return render_template('/views/vehicle_models/form.html', action='create', brands=brands,
                           vehicle_model={"name": name, "description": description, "brand_id": brand_id})

@vehicle_model_bp.route('/<vm_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(vm_id):
    brands = BrandService.get_all().get("brands", [])
    if request.method == 'GET':
        result = VehicleModelService.get_by_id(vm_id)
        if not result["success"]:
            flash(result["message"], 'danger')
            return redirect(url_for('vehicle_models.index'))
        return render_template('/views/vehicle_models/form.html', action='edit',
                               vehicle_model=result["vehicle_model"], brands=brands)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    brand_id = request.form.get('brand_id', '').strip()
    result = VehicleModelService.update(vm_id, name, description, brand_id)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('vehicle_models.index'))
    flash(result["message"], 'danger')
    vm = VehicleModelService.get_by_id(vm_id)
    return render_template('/views/vehicle_models/form.html', action='edit', brands=brands,
                           vehicle_model=vm.get("vehicle_model"))

@vehicle_model_bp.route('/<vm_id>/delete', methods=['POST'])
@role_required('admin')
def delete(vm_id):
    result = VehicleModelService.delete(vm_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('vehicle_models.index'))

@vehicle_model_bp.route('/api/by-brand/<brand_id>', methods=['GET'])
@login_required
def api_by_brand(brand_id):
    result = VehicleModelService.get_by_brand(brand_id)
    data = [{"id": v.id, "name": v.name} for v in result.get("vehicle_models", [])]
    return jsonify(data)
