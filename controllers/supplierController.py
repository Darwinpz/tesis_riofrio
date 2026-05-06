from flask import render_template, request, redirect, url_for, Blueprint, flash
from services.supplierService import SupplierService
from utils.authDecorator import role_required

supplier_bp = Blueprint('suppliers', __name__, url_prefix='/suppliers')

@supplier_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    result = SupplierService.get_all()
    return render_template('/views/suppliers/list.html', suppliers=result.get("suppliers", []))

@supplier_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin')
def create():
    if request.method == 'GET':
        return render_template('/views/suppliers/form.html', action='create', supplier=None)
    name = request.form.get('name', '')
    contact = request.form.get('contact', '')
    phone = request.form.get('phone', '')
    email = request.form.get('email', '')
    address = request.form.get('address', '')
    result = SupplierService.create(name, contact, phone, email, address)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('suppliers.index'))
    flash(result["message"], 'danger')
    return render_template('/views/suppliers/form.html', action='create',
                           supplier={"name": name, "contact": contact, "phone": phone,
                                     "email": email, "address": address})

@supplier_bp.route('/<supplier_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit(supplier_id):
    if request.method == 'GET':
        result = SupplierService.get_by_id(supplier_id)
        if not result["success"]:
            flash(result["message"], 'danger')
            return redirect(url_for('suppliers.index'))
        return render_template('/views/suppliers/form.html', action='edit', supplier=result["supplier"])
    name = request.form.get('name', '')
    contact = request.form.get('contact', '')
    phone = request.form.get('phone', '')
    email = request.form.get('email', '')
    address = request.form.get('address', '')
    result = SupplierService.update(supplier_id, name, contact, phone, email, address)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('suppliers.index'))
    flash(result["message"], 'danger')
    sup_result = SupplierService.get_by_id(supplier_id)
    return render_template('/views/suppliers/form.html', action='edit',
                           supplier=sup_result.get("supplier"))

@supplier_bp.route('/<supplier_id>/delete', methods=['POST'])
@role_required('admin')
def delete(supplier_id):
    result = SupplierService.delete(supplier_id)
    if result["success"]:
        flash(result["message"], 'success')
    else:
        flash(result["message"], 'danger')
    return redirect(url_for('suppliers.index'))
