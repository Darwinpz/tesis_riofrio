from flask import render_template, request, redirect, url_for, Blueprint, flash, session
from services.userService import UserService
from utils.authDecorator import role_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/users', methods=['GET'])
@role_required('admin')
def users():
    result = UserService.get_all_users_with_profile()
    return render_template('/views/admin/users.html', users=result.get("users", []))

@admin_bp.route('/users/<user_id>/edit', methods=['GET', 'POST'])
@role_required('admin')
def edit_user(user_id):
    current_admin_id = session.get("user_id")
    if request.method == 'GET':
        result = UserService.get_user_by_id(user_id)
        if not result["success"]:
            flash(result["message"], 'danger')
            return redirect(url_for('admin.users'))
        return render_template('/views/admin/user_edit.html', profile=result["user"])
    else:
        role = request.form.get('role', '').strip()
        result = UserService.update_user_role(user_id, role)
        if result["success"]:
            flash(result["message"], 'success')
        else:
            flash(result["message"], 'danger')
        return redirect(url_for('admin.users'))

@admin_bp.route('/users/create', methods=['GET', 'POST'])
@role_required('admin')
def create_user():
    if request.method == 'GET':
        return render_template('/views/admin/user_create.html')

    identification = request.form.get('identification', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '')
    role = request.form.get('role', 'client').strip()

    result = UserService.create_user_by_admin(identification, first_name, last_name, email, password, role)
    if result['success']:
        flash(result['message'], 'success')
        return redirect(url_for('admin.users'))
    flash(result['message'], 'danger')
    return render_template('/views/admin/user_create.html',
                           identification=identification, first_name=first_name,
                           last_name=last_name, email=email, role=role)

@admin_bp.route('/users/<user_id>/delete', methods=['POST'])
@role_required('admin')
def delete_user(user_id):
    current_admin_id = session.get("user_id")
    if user_id == current_admin_id:
        flash('No puedes eliminar tu propio usuario', 'danger')
        return redirect(url_for('admin.users'))
    result = UserService.delete_user(user_id)
    if result["success"]:
        flash(result["message"], 'success')
    else:
        flash(result["message"], 'danger')
    return redirect(url_for('admin.users'))
