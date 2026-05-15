import os
from flask import render_template, request, redirect, url_for, Blueprint, flash, jsonify, make_response, current_app
from services.sparePartService import SparePartService
from services.categoryService import CategoryService
from services.supplierService import SupplierService
from services.brandService import BrandService
from services.vehicleModelService import VehicleModelService
from services.stockService import StockService
from utils.authDecorator import login_required, role_required
from utils.reportUtil import generate_stock_report

spare_part_bp = Blueprint('spare_parts', __name__, url_prefix='/spare-parts')

def _get_upload_folder():
    return os.path.join(current_app.static_folder, 'uploads', 'repuestos')

def _lookup_maps():
    brands = {b.id: b.name for b in BrandService.get_all().get("brands", [])}
    vehicle_models = {v.id: v.name for v in VehicleModelService.get_all().get("vehicle_models", [])}
    return brands, vehicle_models

@spare_part_bp.route('/', methods=['GET'])
@login_required
def index():
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', '').strip()
    brand_id = request.args.get('brand_id', '').strip()
    vehicle_model_id = request.args.get('vehicle_model_id', '').strip()
    critical_only = request.args.get('critical_only') == '1'
    result = SparePartService.get_paginated(page=page, per_page=10,
                                            search=search or None,
                                            category_id=category_id or None,
                                            brand_id=brand_id or None,
                                            vehicle_model_id=vehicle_model_id or None,
                                            critical_only=critical_only)
    categories = CategoryService.get_all().get("categories", [])
    brands = BrandService.get_all().get("brands", [])
    vehicle_models_list = VehicleModelService.get_all().get("vehicle_models", [])
    brands_map, vm_map = _lookup_maps()
    return render_template('/views/spare_parts/list.html',
                           parts=result.get("parts", []),
                           total=result.get("total", 0),
                           page=result.get("page", 1),
                           total_pages=result.get("total_pages", 1),
                           search=search,
                           category_id=category_id,
                           brand_id=brand_id,
                           vehicle_model_id=vehicle_model_id,
                           critical_only=critical_only,
                           categories=categories,
                           brands=brands,
                           vehicle_models_list=vehicle_models_list,
                           brands_map=brands_map,
                           vm_map=vm_map)

@spare_part_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def create():
    categories = CategoryService.get_all().get("categories", [])
    suppliers = SupplierService.get_all().get("suppliers", [])
    brands = BrandService.get_all().get("brands", [])
    vehicle_models_list = VehicleModelService.get_all().get("vehicle_models", [])
    if request.method == 'GET':
        return render_template('/views/spare_parts/form.html', action='create',
                               part=None, categories=categories, suppliers=suppliers,
                               brands=brands, vehicle_models_list=vehicle_models_list)
    imagen_file = request.files.get('imagen')
    result = SparePartService.create(request.form.to_dict(), imagen_file, _get_upload_folder())
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('spare_parts.index'))
    flash(result["message"], 'danger')
    return render_template('/views/spare_parts/form.html', action='create',
                           part=request.form.to_dict(), categories=categories, suppliers=suppliers,
                           brands=brands, vehicle_models_list=vehicle_models_list)

@spare_part_bp.route('/<part_id>', methods=['GET'])
@login_required
def detail(part_id):
    result = SparePartService.get_by_id(part_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('spare_parts.index'))
    part = result["part"]
    movements = StockService.get_movements_by_part(part_id).get("movements", [])
    categories = {c.id: c.name for c in CategoryService.get_all().get("categories", [])}
    suppliers = {s.id: s.name for s in SupplierService.get_all().get("suppliers", [])}
    brands_map, vm_map = _lookup_maps()
    return render_template('/views/spare_parts/detail.html', part=part,
                           movements=movements, categories=categories, suppliers=suppliers,
                           brands_map=brands_map, vm_map=vm_map)

@spare_part_bp.route('/<part_id>/edit', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def edit(part_id):
    categories = CategoryService.get_all().get("categories", [])
    suppliers = SupplierService.get_all().get("suppliers", [])
    brands = BrandService.get_all().get("brands", [])
    vehicle_models_list = VehicleModelService.get_all().get("vehicle_models", [])
    if request.method == 'GET':
        result = SparePartService.get_by_id(part_id)
        if not result["success"]:
            flash(result["message"], 'danger')
            return redirect(url_for('spare_parts.index'))
        return render_template('/views/spare_parts/form.html', action='edit',
                               part=result["part"], categories=categories, suppliers=suppliers,
                               brands=brands, vehicle_models_list=vehicle_models_list)
    imagen_file = request.files.get('imagen')
    result = SparePartService.update(part_id, request.form.to_dict(), imagen_file, _get_upload_folder())
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('spare_parts.detail', part_id=part_id))
    flash(result["message"], 'danger')
    part_result = SparePartService.get_by_id(part_id)
    return render_template('/views/spare_parts/form.html', action='edit',
                           part=part_result.get("part"), categories=categories, suppliers=suppliers,
                           brands=brands, vehicle_models_list=vehicle_models_list)

@spare_part_bp.route('/<part_id>/delete', methods=['POST'])
@role_required('admin')
def delete(part_id):
    result = SparePartService.delete(part_id)
    if result["success"]:
        flash(result["message"], 'success')
    else:
        flash(result["message"], 'danger')
    return redirect(url_for('spare_parts.index'))

@spare_part_bp.route('/<part_id>/deactivate', methods=['POST'])
@role_required('admin')
def deactivate(part_id):
    result = SparePartService.deactivate(part_id)
    if result["success"]:
        flash(result["message"], 'success')
    else:
        flash(result["message"], 'danger')
    return redirect(url_for('spare_parts.index'))

@spare_part_bp.route('/report', methods=['GET'])
@role_required('admin', 'operator')
def report():
    search = request.args.get('search', '').strip() or None
    category_id = request.args.get('category_id', '').strip() or None
    brand_id = request.args.get('brand_id', '').strip() or None
    vehicle_model_id = request.args.get('vehicle_model_id', '').strip() or None
    critical_only = request.args.get('critical_only') == '1'

    result = SparePartService.get_paginated(page=1, per_page=5000,
                                            search=search,
                                            category_id=category_id,
                                            brand_id=brand_id,
                                            vehicle_model_id=vehicle_model_id,
                                            critical_only=critical_only)
    parts = result.get("parts", [])

    categories_map = {c.id: c.name for c in CategoryService.get_all().get("categories", [])}
    brands_map, _ = _lookup_maps()

    filters = []
    if search:
        filters.append(f"Búsqueda: {search}")
    if category_id:
        filters.append(f"Categoría: {categories_map.get(category_id, category_id)}")
    if brand_id:
        filters.append(f"Marca: {brands_map.get(brand_id, brand_id)}")
    if critical_only:
        filters.append("Solo stock crítico")
    filter_desc = " · ".join(filters) if filters else ""

    pdf = generate_stock_report(parts, critical_only=critical_only,
                                category_map=categories_map, brand_map=brands_map,
                                filter_desc=filter_desc)
    resp = make_response(pdf)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'inline; filename="inventario_repuestos.pdf"'
    return resp


@spare_part_bp.route('/api/all', methods=['GET'])
@role_required('admin', 'operator')
def api_all():
    result = SparePartService.get_all_active()
    parts_data = [{"id": p.id, "code": p.code, "name": p.name,
                   "stock_actual": p.stock_actual, "precio_venta": p.precio_venta}
                  for p in result.get("parts", [])]
    return jsonify(parts_data)
