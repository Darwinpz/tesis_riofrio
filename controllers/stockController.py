import os
from flask import render_template, request, redirect, url_for, Blueprint, flash, session, make_response, current_app, Response
from services.stockService import StockService
from services.sparePartService import SparePartService
from services.supplierService import SupplierService
from services.userService import UserService
from utils.authDecorator import role_required
from utils.reportUtil import generate_movements_report, generate_exit_comprobante
from repositories.stockMovementRepository import StockMovementRepository
from repositories.userRepository import UserRepository
from repositories.personRepository import PersonRepository

stock_bp = Blueprint('stock', __name__, url_prefix='/stock')


def _upload_folder():
    return os.path.join(current_app.static_folder, "uploads", "facturas")


@stock_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    page = int(request.args.get('page', 1))
    spare_part_id = request.args.get('spare_part_id', '').strip() or None
    movement_type = request.args.get('movement_type', '').strip() or None
    start_date = request.args.get('start_date', '').strip() or None
    end_date = request.args.get('end_date', '').strip() or None
    open_comprobante = request.args.get('open_comprobante', '').strip()

    result = StockService.get_paginated(
        page=page, per_page=15,
        spare_part_id=spare_part_id,
        movement_type=movement_type,
        start_date_str=start_date,
        end_date_str=end_date
    )
    parts = SparePartService.get_all_active().get("parts", [])

    parts_map = {p.id: p.name for p in parts}
    movements = result.get("movements", [])
    for m in movements:
        m.spare_part_name = parts_map.get(m.spare_part_id, m.spare_part_id)

    return render_template('/views/stock/list.html',
                           movements=movements,
                           parts=parts,
                           total=result.get("total", 0),
                           page=result.get("page", 1),
                           total_pages=result.get("total_pages", 1),
                           filter_part=spare_part_id or '',
                           filter_type=movement_type or '',
                           filter_start=start_date or '',
                           filter_end=end_date or '',
                           open_comprobante=open_comprobante)


@stock_bp.route('/report', methods=['GET'])
@role_required('admin', 'operator')
def report():
    spare_part_id = request.args.get('spare_part_id', '').strip() or None
    movement_type = request.args.get('movement_type', '').strip() or None
    start_date = request.args.get('start_date', '').strip() or None
    end_date = request.args.get('end_date', '').strip() or None

    result = StockService.get_all_for_report(spare_part_id, movement_type, start_date, end_date)
    movements = result.get("movements", [])

    all_parts = SparePartService.get_all_active().get("parts", [])
    parts_map = {p.id: f"{p.code} — {p.name}" for p in all_parts}

    filters = []
    if spare_part_id:
        part_label = parts_map.get(spare_part_id, spare_part_id)
        filters.append(f"Repuesto: {part_label}")
    if movement_type:
        filters.append(f"Tipo: {'Entrada' if movement_type == 'entrada' else 'Salida'}")
    filter_desc = " · ".join(filters) if filters else ""

    pdf = generate_movements_report(movements, parts_map,
                                    start_date=start_date, end_date=end_date,
                                    filter_desc=filter_desc)
    resp = make_response(pdf)
    resp.headers['Content-Type'] = 'application/pdf'
    resp.headers['Content-Disposition'] = 'inline; filename="movimientos_stock.pdf"'
    return resp


@stock_bp.route('/entry', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def entry():
    parts = SparePartService.get_all_active().get("parts", [])
    suppliers = SupplierService.get_all().get("suppliers", [])
    if request.method == 'GET':
        preselect = request.args.get('part_id', '')
        return render_template('/views/stock/entry.html', parts=parts, suppliers=suppliers,
                               preselect=preselect)

    spare_part_id = request.form.get('spare_part_id', '').strip()
    try:
        quantity = int(request.form.get('quantity', 0))
    except ValueError:
        quantity = 0
    motive = request.form.get('motive', '').strip()
    note = request.form.get('note', '').strip()
    supplier_id = request.form.get('supplier_id', '').strip() or None
    user_id = session.get("user_id")
    attachment_file = request.files.get('attachment')

    result = StockService.register_entry(spare_part_id, quantity, motive, note, user_id,
                                         supplier_id=supplier_id,
                                         attachment_file=attachment_file,
                                         upload_folder=_upload_folder())
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('stock.index'))
    flash(result["message"], 'danger')
    return render_template('/views/stock/entry.html', parts=parts, suppliers=suppliers,
                           preselect=spare_part_id)


@stock_bp.route('/exit', methods=['GET', 'POST'])
@role_required('admin', 'operator')
def exit():
    parts = SparePartService.get_all_active().get("parts", [])
    clients = UserService.get_clients().get("clients", [])
    suppliers = SupplierService.get_all().get("suppliers", [])
    if request.method == 'GET':
        preselect = request.args.get('part_id', '')
        return render_template('/views/stock/exit.html', parts=parts, preselect=preselect,
                               clients=clients, suppliers=suppliers)

    spare_part_id = request.form.get('spare_part_id', '').strip()
    try:
        quantity = int(request.form.get('quantity', 0))
    except ValueError:
        quantity = 0
    motive = request.form.get('motive', '').strip()
    note = request.form.get('note', '').strip()
    recipient_name = request.form.get('recipient_name', '').strip() or None
    recipient_type = request.form.get('recipient_type', '').strip() or None
    user_id = session.get("user_id")

    result = StockService.register_exit(spare_part_id, quantity, motive, note, user_id,
                                         recipient_name=recipient_name,
                                         recipient_type=recipient_type)
    if result["success"]:
        flash(result["message"], 'success')
        movement_id = result.get("movement_id")
        return redirect(url_for('stock.index', open_comprobante=movement_id or ''))
    flash(result["message"], 'danger')
    return render_template('/views/stock/exit.html', parts=parts, preselect=spare_part_id,
                           clients=clients, suppliers=suppliers)


@stock_bp.route('/<movement_id>/comprobante', methods=['GET'])
@role_required('admin', 'operator')
def comprobante(movement_id):
    movement = StockMovementRepository.find_by_id(movement_id)
    if not movement:
        flash('Movimiento no encontrado', 'danger')
        return redirect(url_for('stock.index'))

    all_parts = SparePartService.get_all_active().get("parts", [])
    parts_map = {p.id: p for p in all_parts}
    part = parts_map.get(movement.spare_part_id)
    part_name = f"{part.code} — {part.name}" if part else movement.spare_part_id

    user_id = session.get("user_id")
    user = UserRepository.find_by_id(user_id)
    person = PersonRepository.find_by_user_id(user_id)
    if person:
        user_name = f"{person.first_name} {person.last_name}".strip()
    else:
        user_name = user.email if user else user_id

    pdf_bytes = generate_exit_comprobante(movement, part_name, user_name)
    return Response(pdf_bytes, mimetype='application/pdf',
                    headers={"Content-Disposition": f"inline; filename=comprobante-salida-{movement_id}.pdf"})
