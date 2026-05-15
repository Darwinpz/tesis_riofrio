import os
from flask import render_template, request, redirect, url_for, Blueprint, flash, current_app
from werkzeug.utils import secure_filename
from services.brandService import BrandService
from utils.authDecorator import role_required

_BRAND_IMG_EXTS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

def _save_brand_image(file, brand_name: str):
    if not file or not file.filename:
        return None
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in _BRAND_IMG_EXTS:
        return None
    upload_dir = os.path.join(current_app.static_folder, "uploads", "brands")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(f"brand_{brand_name}.{ext}")
    file.save(os.path.join(upload_dir, filename))
    return f"uploads/brands/{filename}"

brand_bp = Blueprint('brands', __name__, url_prefix='/brands')

@brand_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    result = BrandService.get_all()
    return render_template('/views/brands/list.html', brands=result.get("brands", []))

@brand_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin')
def create():
    if request.method == 'GET':
        return render_template('/views/brands/form.html', action='create', brand=None)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    imagen_path = _save_brand_image(request.files.get('imagen'), name)
    result = BrandService.create(name, description, imagen_path)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('brands.index'))
    flash(result["message"], 'danger')
    return render_template('/views/brands/form.html', action='create',
                           brand={"name": name, "description": description})

@brand_bp.route('/<brand_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(brand_id):
    if request.method == 'GET':
        result = BrandService.get_by_id(brand_id)
        if not result["success"]:
            flash(result["message"], 'danger')
            return redirect(url_for('brands.index'))
        return render_template('/views/brands/form.html', action='edit', brand=result["brand"])
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    imagen_file = request.files.get('imagen')
    imagen_path = _save_brand_image(imagen_file, name) if imagen_file and imagen_file.filename else None
    result = BrandService.update(brand_id, name, description, imagen_path)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('brands.index'))
    flash(result["message"], 'danger')
    b = BrandService.get_by_id(brand_id)
    return render_template('/views/brands/form.html', action='edit', brand=b.get("brand"))

@brand_bp.route('/<brand_id>/delete', methods=['POST'])
@role_required('admin')
def delete(brand_id):
    result = BrandService.delete(brand_id)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('brands.index'))
