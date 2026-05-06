from flask import render_template, request, redirect, url_for, Blueprint, flash
from services.categoryService import CategoryService
from utils.authDecorator import role_required

category_bp = Blueprint('categories', __name__, url_prefix='/categories')

@category_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    result = CategoryService.get_all()
    return render_template('/views/categories/list.html', categories=result.get("categories", []))

@category_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin')
def create():
    if request.method == 'GET':
        return render_template('/views/categories/form.html', action='create', category=None)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    result = CategoryService.create(name, description)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('categories.index'))
    flash(result["message"], 'danger')
    return render_template('/views/categories/form.html', action='create',
                           category={"name": name, "description": description})

@category_bp.route('/<category_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(category_id):
    if request.method == 'GET':
        result = CategoryService.get_by_id(category_id)
        if not result["success"]:
            flash(result["message"], 'danger')
            return redirect(url_for('categories.index'))
        return render_template('/views/categories/form.html', action='edit', category=result["category"])
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    result = CategoryService.update(category_id, name, description)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('categories.index'))
    flash(result["message"], 'danger')
    cat_result = CategoryService.get_by_id(category_id)
    return render_template('/views/categories/form.html', action='edit',
                           category=cat_result.get("category"))

@category_bp.route('/<category_id>/delete', methods=['POST'])
@role_required('admin')
def delete(category_id):
    result = CategoryService.delete(category_id)
    if result["success"]:
        flash(result["message"], 'success')
    else:
        flash(result["message"], 'danger')
    return redirect(url_for('categories.index'))
