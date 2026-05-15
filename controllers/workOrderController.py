import os
from flask import render_template, request, redirect, url_for, Blueprint, flash, session, Response, current_app
from services.workOrderService import WorkOrderService
from services.userService import UserService
from services.sparePartService import SparePartService
from services.brandService import BrandService
from services.vehicleModelService import VehicleModelService
from models.workOrderModel import WorkOrderModel
from utils.authDecorator import login_required, role_required
from utils.reportUtil import generate_work_order_pdf, generate_reception_receipt, generate_work_orders_list_pdf
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository


def _user_full_name(user_id: str, user_email: str = "") -> str:
    person = PersonRepository.find_by_user_id(user_id)
    if person:
        return f"{person.first_name} {person.last_name}".strip()
    return user_email or user_id

work_order_bp = Blueprint('work_orders', __name__, url_prefix='/work-orders')


def _order_form_data():
    clients = UserService.get_clients().get("clients", [])
    mechanics = UserService.get_mechanics().get("mechanics", [])
    parts = SparePartService.get_all_active().get("parts", [])
    brands = BrandService.get_all().get("brands", [])
    vehicle_models_list = VehicleModelService.get_all().get("vehicle_models", [])
    return clients, mechanics, parts, brands, vehicle_models_list


def _upload_folder():
    return os.path.join(current_app.static_folder, "uploads", "ordenes")


def _clients_map():
    return {c["id"]: c["full_name"] for c in UserService.get_clients().get("clients", [])}

def _mechanics_map():
    return {m["id"]: m["full_name"] for m in UserService.get_mechanics().get("mechanics", [])}


@work_order_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '').strip() or None
    status = request.args.get('status', '').strip() or None
    result = WorkOrderService.get_paginated(page=page, per_page=10, search=search, status=status)

    c_map = _clients_map()
    m_map = _mechanics_map()
    brands_map = {b.name: b for b in BrandService.get_all().get("brands", [])}

    orders = result.get("orders", [])
    for o in orders:
        o.client_name = c_map.get(o.client_id, o.client_id)
        o.mechanic_name = m_map.get(o.mechanic_id, "—") if o.mechanic_id else "—"

    return render_template('/views/work_orders/list.html',
                           orders=orders,
                           total=result.get("total", 0),
                           page=result.get("page", 1),
                           total_pages=result.get("total_pages", 1),
                           filter_search=search or '',
                           filter_status=status or '',
                           brands_map=brands_map)


@work_order_bp.route('/create', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def create():
    clients, mechanics, parts, brands, vehicle_models_list = _order_form_data()

    if request.method == 'GET':
        return render_template('/views/work_orders/create.html',
                               clients=clients, mechanics=mechanics, parts=parts,
                               brands=brands, vehicle_models_list=vehicle_models_list)

    parts_json = request.form.get('parts_json', '[]')
    operator_id = session.get("user_id")
    photo_files = request.files.getlist('vehicle_photos')

    result = WorkOrderService.create(
        request.form.to_dict(), parts_json, operator_id,
        photo_files=photo_files, upload_folder=_upload_folder()
    )
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('work_orders.detail', order_id=result["order_id"]))
    flash(result["message"], 'danger')
    return render_template('/views/work_orders/create.html',
                           clients=clients, mechanics=mechanics, parts=parts,
                           brands=brands, vehicle_models_list=vehicle_models_list)


@work_order_bp.route('/<order_id>', methods=['GET'])
@login_required
def detail(order_id):
    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.index'))

    order = result["order"]
    current_user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(current_user_id)

    if current_user and current_user.role == 'client' and order.client_id != current_user_id:
        flash('No tienes permiso para ver este ingreso', 'danger')
        return redirect(url_for('work_orders.my_orders'))

    if current_user and current_user.role == 'mechanic' and order.mechanic_id != current_user_id:
        flash('No tienes permiso para ver este ingreso', 'danger')
        return redirect(url_for('work_orders.my_orders'))

    c_map = _clients_map()
    m_map = _mechanics_map()
    order.client_name = c_map.get(order.client_id, order.client_id)
    order.mechanic_name = m_map.get(order.mechanic_id, "—") if order.mechanic_id else "—"

    # Compute advance context
    can_advance = order.can_user_advance(current_user.role) if current_user else False
    adv = WorkOrderModel.STATUS_ADVANCE_LABELS.get(order.canonical_status, ("", ""))

    # Compute edit access
    can_edit = False
    if current_user:
        if current_user.role in ('admin', 'operator'):
            can_edit = not order.is_closed and order.canonical_status != 'pago_pendiente'

    can_register_work = bool(
        current_user and current_user.role == 'mechanic' and
        order.mechanic_id == current_user_id and
        order.canonical_status in ('diagnostico', 'en_reparacion')
    )

    can_revert = order.can_user_revert(current_user.role) if current_user else False

    can_cancel = False
    if current_user and not order.is_closed:
        if current_user.role in ("admin", "operator"):
            can_cancel = True
        elif current_user.role == "client" and order.canonical_status == "presupuesto" and order.client_id == current_user_id:
            can_cancel = True

    parts_map = {p.id: p for p in SparePartService.get_all_active().get("parts", [])}
    return render_template('/views/work_orders/detail.html',
                           order=order,
                           parts_map=parts_map,
                           clients_map=c_map,
                           can_advance=can_advance,
                           advance_label=adv[0],
                           advance_description=adv[1],
                           can_edit=can_edit,
                           can_revert=can_revert,
                           can_cancel=can_cancel,
                           can_register_work=can_register_work,
                           current_user=current_user,
                           STATUS_LABELS=WorkOrderModel.STATUS_LABELS)


@work_order_bp.route('/<order_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(order_id):
    user_id = session.get("user_id")
    current_user_obj = UserRepository.find_by_id(user_id)

    if not current_user_obj or current_user_obj.role == 'client':
        flash('Sin permiso', 'danger')
        return redirect(url_for('work_orders.index'))

    # Mechanics use the dedicated work-registration page
    if current_user_obj.role == 'mechanic':
        return redirect(url_for('work_orders.mechanic_work', order_id=order_id))

    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.index'))

    order = result["order"]

    if current_user_obj.role in ('admin', 'operator'):
        if order.is_closed or order.canonical_status == 'pago_pendiente':
            flash('No se puede editar un ingreso en Pago Pendiente o Entregado', 'danger')
            return redirect(url_for('work_orders.detail', order_id=order_id))

    clients, mechanics, parts, brands, vehicle_models_list = _order_form_data()

    if request.method == 'GET':
        return render_template('/views/work_orders/edit.html',
                               order=order, clients=clients, mechanics=mechanics,
                               parts=parts, brands=brands,
                               vehicle_models_list=vehicle_models_list)

    parts_json = request.form.get('parts_json', '[]')
    photo_files = request.files.getlist('vehicle_photos')
    result = WorkOrderService.update(order_id, request.form.to_dict(), parts_json,
                                     photo_files=photo_files, upload_folder=_upload_folder())
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('work_orders.detail', order_id=order_id))
    flash(result["message"], 'danger')
    return render_template('/views/work_orders/edit.html',
                           order=order, clients=clients, mechanics=mechanics,
                           parts=parts, brands=brands,
                           vehicle_models_list=vehicle_models_list)


@work_order_bp.route('/<order_id>/mechanic-work', methods=['GET', 'POST'])
@login_required
def mechanic_work(order_id):
    user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(user_id)

    if not current_user or current_user.role not in ('mechanic', 'admin', 'operator'):
        flash('Sin permiso', 'danger')
        return redirect(url_for('work_orders.detail', order_id=order_id))

    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.my_orders'))

    order = result["order"]

    if current_user.role == 'mechanic' and order.mechanic_id != user_id:
        flash('No eres el mecánico asignado a este ingreso', 'danger')
        return redirect(url_for('work_orders.my_orders'))

    if order.canonical_status not in ('diagnostico', 'en_reparacion'):
        flash('Solo puedes registrar trabajo en Diagnóstico o En Reparación', 'danger')
        return redirect(url_for('work_orders.detail', order_id=order_id))

    parts = SparePartService.get_all_active().get("parts", [])

    if request.method == 'GET':
        c_map = _clients_map()
        order.client_name = c_map.get(order.client_id, order.client_id)
        return render_template('/views/work_orders/mechanic_work.html',
                               order=order, parts=parts)

    parts_json = request.form.get('parts_json', '[]')
    labor_cost_str = request.form.get('labor_cost', '0')
    notes = request.form.get('notes', '').strip()
    photo_files = request.files.getlist('evidence_photos')

    result = WorkOrderService.update_mechanic_work(
        order_id, user_id, current_user.role, parts_json, labor_cost_str, notes,
        photo_files=photo_files, upload_folder=_upload_folder()
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    if result["success"]:
        return redirect(url_for('work_orders.detail', order_id=order_id))
    c_map = _clients_map()
    order.client_name = c_map.get(order.client_id, order.client_id)
    return render_template('/views/work_orders/mechanic_work.html', order=order, parts=parts)


@work_order_bp.route('/<order_id>/advance', methods=['POST'])
@login_required
def advance(order_id):
    user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(user_id)
    if not current_user:
        flash('Sesión inválida', 'danger')
        return redirect(url_for('work_orders.index'))
    reason = request.form.get('reason', '').strip()
    user_name = _user_full_name(user_id, current_user.email)
    result = WorkOrderService.advance_status(order_id, current_user.role, user_id,
                                             user_name=user_name, reason=reason)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('work_orders.detail', order_id=order_id))


@work_order_bp.route('/<order_id>/revert', methods=['POST'])
@login_required
def revert(order_id):
    user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(user_id)
    if not current_user or current_user.role not in ('admin', 'operator'):
        flash('Sin permiso para retroceder estados', 'danger')
        return redirect(url_for('work_orders.detail', order_id=order_id))
    reason = request.form.get('reason', '').strip()
    user_name = _user_full_name(user_id, current_user.email)
    result = WorkOrderService.revert_status(order_id, current_user.role, user_id,
                                            user_name=user_name, reason=reason)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('work_orders.detail', order_id=order_id))


@work_order_bp.route('/<order_id>/cancel', methods=['POST'])
@login_required
def cancel(order_id):
    user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(user_id)
    if not current_user:
        flash('Sesión inválida', 'danger')
        return redirect(url_for('work_orders.detail', order_id=order_id))
    reason = request.form.get('reason', '').strip()
    user_name = _user_full_name(user_id, current_user.email)
    result = WorkOrderService.cancel_order(order_id, current_user.role, user_id,
                                           user_name=user_name, reason=reason)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('work_orders.detail', order_id=order_id))


@work_order_bp.route('/<order_id>/delete-photo', methods=['POST'])
@login_required
def delete_photo(order_id):
    user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(user_id)
    if not current_user:
        flash('Sesión inválida', 'danger')
        return redirect(url_for('work_orders.detail', order_id=order_id))
    photo_type = request.form.get('photo_type', '')
    photo_path = request.form.get('photo_path', '')
    result = WorkOrderService.delete_photo(
        order_id, photo_type, photo_path,
        current_user.role, user_id,
        static_folder=current_app.static_folder
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('work_orders.detail', order_id=order_id))


@work_order_bp.route('/<order_id>/upload-payment', methods=['POST'])
@login_required
def upload_payment(order_id):
    user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(user_id)
    if not current_user:
        flash('Sesión inválida', 'danger')
        return redirect(url_for('work_orders.detail', order_id=order_id))
    proof_file = request.files.get('payment_proof')
    result = WorkOrderService.upload_payment_proof(
        order_id, user_id, current_user.role,
        proof_file=proof_file, upload_folder=_upload_folder()
    )
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('work_orders.detail', order_id=order_id))


@work_order_bp.route('/<order_id>/pdf', methods=['GET'])
@login_required
def pdf(order_id):
    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.index'))

    order = result["order"]
    client_name = _clients_map().get(order.client_id, "Cliente")
    pdf_bytes = generate_work_order_pdf(order, client_name)
    return Response(pdf_bytes, mimetype='application/pdf',
                    headers={"Content-Disposition": f"attachment; filename=Ingreso-{order.number}.pdf"})


@work_order_bp.route('/<order_id>/receipt', methods=['GET'])
@login_required
def receipt(order_id):
    result = WorkOrderService.get_by_id(order_id)
    if not result["success"]:
        flash(result["message"], 'danger')
        return redirect(url_for('work_orders.index'))

    order = result["order"]
    c_map = _clients_map()
    m_map = _mechanics_map()
    client_name = c_map.get(order.client_id, "Cliente")
    mechanic_name = m_map.get(order.mechanic_id, "") if order.mechanic_id else ""
    pdf_bytes = generate_reception_receipt(order, client_name, mechanic_name)
    return Response(pdf_bytes, mimetype='application/pdf',
                    headers={"Content-Disposition": f"inline; filename=Recepcion-{order.number}.pdf"})


@work_order_bp.route('/report', methods=['GET'])
@role_required('admin', 'operator')
def report():
    search = request.args.get('search', '').strip() or None
    status = request.args.get('status', '').strip() or None
    result = WorkOrderService.get_paginated(page=1, per_page=1000, search=search, status=status)
    orders = result.get("orders", [])
    c_map = _clients_map()
    pdf_bytes = generate_work_orders_list_pdf(orders, c_map,
                                              filter_search=search or '',
                                              filter_status=status or '')
    filename = f"Reporte-Ingresos-{__import__('datetime').datetime.now().strftime('%Y%m%d')}.pdf"
    return Response(pdf_bytes, mimetype='application/pdf',
                    headers={"Content-Disposition": f"inline; filename={filename}"})


@work_order_bp.route('/my-orders', methods=['GET'])
@login_required
def my_orders():
    user_id = session.get("user_id")
    current_user = UserRepository.find_by_id(user_id)

    if current_user and current_user.role == 'mechanic':
        result = WorkOrderService.get_by_mechanic(user_id)
        title = "Mis Ingresos Asignados"
    else:
        result = WorkOrderService.get_by_client(user_id)
        title = "Mis Ingresos de Taller"

    orders = result.get("orders", [])
    return render_template('/views/work_orders/my_orders.html', orders=orders, title=title)
