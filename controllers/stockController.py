import os
from flask import render_template, request, redirect, url_for, Blueprint, flash, session, current_app
from services.stockService import StockService
from services.sparePartService import SparePartService
from services.supplierService import SupplierService
from utils.authDecorator import role_required

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
                           filter_end=end_date or '')


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
    if request.method == 'GET':
        preselect = request.args.get('part_id', '')
        return render_template('/views/stock/exit.html', parts=parts, preselect=preselect)

    spare_part_id = request.form.get('spare_part_id', '').strip()
    try:
        quantity = int(request.form.get('quantity', 0))
    except ValueError:
        quantity = 0
    motive = request.form.get('motive', '').strip()
    note = request.form.get('note', '').strip()
    user_id = session.get("user_id")
    attachment_file = request.files.get('attachment')

    result = StockService.register_exit(spare_part_id, quantity, motive, note, user_id,
                                         attachment_file=attachment_file,
                                         upload_folder=_upload_folder())
    if result["success"]:
        flash(result["message"], 'success')
        return redirect(url_for('stock.index'))
    flash(result["message"], 'danger')
    return render_template('/views/stock/exit.html', parts=parts, preselect=spare_part_id)
