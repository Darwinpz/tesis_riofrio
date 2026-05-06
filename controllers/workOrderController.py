from flask import render_template, request, redirect, url_for, Blueprint, flash, session, Response
from services.workOrderService import WorkOrderService
from services.userService import UserService
from services.sparePartService import SparePartService
from services.categoryService import CategoryService
from utils.authDecorator import login_required, role_required
from utils.reportUtil import generate_work_order_pdf

work_order_bp = Blueprint('work_orders', __name__, url_prefix='/work-orders')

@work_order_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '').strip() or None
    status = request.args.get('status', '').strip() or None
    result = WorkOrderService.get_paginated(page=page, per_page=10, search=search, status=status)

    clients_result = UserService.get_clients()
    clients_map = {c["id"]: c["full_name"] for c in clients_result.get("clients", [])}

    orders = result.get("orders", [])
    for o in orders:
        o.client_name = clients_map.get(o.client_id, o.client_id)

    return render_template('/views/work_orders/list.html',
                           orders=orders,
                           total=result.get("total", 0),
                           page=result.get("page", 1),
                           total_pages=result.get("total_pages", 1),
                           filter_search=search or '',
                           filter_status=status or '')

@work_order_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def create():
    clients = UserService.get_clients().get("clients", [])
    parts = SparePartService.get_all_active().get("parts", [])
    if request.method == 'GET':
        return render_template('/views/work_orders/create.html', clients=clients, parts=parts)

    parts_json = request.form.get('parts_json', '[]')
    operator_id = session.get("user_id")
    result = WorkOrderService.create(request.form.to_dict(), parts_json, operator_id)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('work_orders.detail', order_id=result["order_id"]))
    flash(result["message"], 'danger')
    return render_template('/views/work_orders/create.html', clients=clients, parts=parts)

@work_order_bp.route('/<order_id>', methods=['GET'])
@login_required
def detail(order_id):
    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.index'))

    order = result["order"]
    current_user_id = session.get("user_id")

    # Los clientes solo ven sus propias órdenes
    from repositories.userRepository import UserRepository
    current_user = UserRepository.find_by_id(current_user_id)
    if current_user and current_user.role == 'client' and order.client_id != current_user_id:
        flash('No tienes permiso para ver esta orden', 'danger')
        return redirect(url_for('work_orders.my_orders'))

    clients_result = UserService.get_clients()
    clients_map = {c["id"]: c["full_name"] for c in clients_result.get("clients", [])}
    order.client_name = clients_map.get(order.client_id, order.client_id)

    parts_map = {p.id: p for p in SparePartService.get_all_active().get("parts", [])}
    return render_template('/views/work_orders/detail.html', order=order,
                           parts_map=parts_map, clients_map=clients_map)

@work_order_bp.route('/<order_id>/edit', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def edit(order_id):
    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.index'))

    order = result["order"]
    clients = UserService.get_clients().get("clients", [])
    parts = SparePartService.get_all_active().get("parts", [])

    if request.method == 'GET':
        return render_template('/views/work_orders/edit.html',
                               order=order, clients=clients, parts=parts)

    parts_json = request.form.get('parts_json', '[]')
    result = WorkOrderService.update(order_id, request.form.to_dict(), parts_json)
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('work_orders.detail', order_id=order_id))
    flash(result["message"], 'danger')
    return render_template('/views/work_orders/edit.html',
                           order=order, clients=clients, parts=parts)

@work_order_bp.route('/<order_id>/close', methods=['POST'])
@role_required('admin', 'operator')
def close(order_id):
    user_id = session.get("user_id")
    result = WorkOrderService.close_order(order_id, user_id)
    if result["success"]:
        flash(result["message"], 'success')
    else:
        flash(result["message"], 'danger')
    return redirect(url_for('work_orders.detail', order_id=order_id))

@work_order_bp.route('/<order_id>/pdf', methods=['GET'])
@login_required
def pdf(order_id):
    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.index'))

    order = result["order"]
    clients_result = UserService.get_clients()
    clients_map = {c["id"]: c["full_name"] for c in clients_result.get("clients", [])}
    client_name = clients_map.get(order.client_id, "Cliente")

    pdf_bytes = generate_work_order_pdf(order, client_name)
    return Response(pdf_bytes, mimetype='application/pdf',
                    headers={"Content-Disposition": f"attachment; filename=OT-{order.number}.pdf"})

@work_order_bp.route('/my-orders', methods=['GET'])
@login_required
def my_orders():
    user_id = session.get("user_id")
    result = WorkOrderService.get_by_client(user_id)
    orders = result.get("orders", [])
    return render_template('/views/work_orders/my_orders.html', orders=orders)
