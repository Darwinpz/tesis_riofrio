import os
from typing import Dict
from datetime import datetime
from werkzeug.utils import secure_filename
from models.stockMovementModel import StockMovementModel
from repositories.stockMovementRepository import StockMovementRepository
from repositories.sparePartRepository import SparePartRepository

ALLOWED_ATTACH_EXT = {"pdf", "png", "jpg", "jpeg", "gif", "webp"}

def _allowed_attach(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_ATTACH_EXT

def _save_attachment(file, upload_folder: str, prefix: str) -> str | None:
    if not file or not file.filename or not _allowed_attach(file.filename):
        return None
    os.makedirs(upload_folder, exist_ok=True)
    filename = secure_filename(f"{prefix}_{file.filename}")
    file.save(os.path.join(upload_folder, filename))
    return f"uploads/facturas/{filename}"

class StockService:

    @staticmethod
    def get_paginated(page: int = 1, per_page: int = 15, spare_part_id: str = None,
                      movement_type: str = None, start_date_str: str = None,
                      end_date_str: str = None) -> Dict:
        try:
            start_date = None
            end_date = None
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            movements, total = StockMovementRepository.find_paginated(
                page, per_page, spare_part_id, movement_type, start_date, end_date
            )
            total_pages = max(1, (total + per_page - 1) // per_page)
            return {"success": True, "movements": movements, "total": total,
                    "page": page, "per_page": per_page, "total_pages": total_pages}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener movimientos: {e}"}

    @staticmethod
    def register_entry(spare_part_id: str, quantity: int, motive: str, note: str,
                       user_id: str, attachment_file=None, upload_folder: str = None) -> Dict:
        if not spare_part_id:
            return {"success": False, "message": "Debe seleccionar un repuesto"}
        if quantity <= 0:
            return {"success": False, "message": "La cantidad debe ser mayor a cero"}
        if motive not in StockMovementModel.ENTRY_MOTIVES:
            return {"success": False, "message": "Motivo de entrada inválido"}
        try:
            part = SparePartRepository.find_by_id(spare_part_id)
            if not part:
                return {"success": False, "message": "Repuesto no encontrado"}
            attachment_path = _save_attachment(attachment_file, upload_folder,
                                               f"entrada_{spare_part_id}") if upload_folder else None
            new_stock = part.stock_actual + quantity
            SparePartRepository.update_stock(spare_part_id, new_stock)
            movement = StockMovementModel(
                spare_part_id=spare_part_id,
                movement_type="entrada",
                quantity=quantity,
                motive=motive,
                note=note.strip() if note else None,
                user_id=user_id,
                attachment_path=attachment_path
            )
            StockMovementRepository.create(movement)
            return {"success": True, "message": f"Entrada registrada. Nuevo stock: {new_stock}"}
        except Exception as e:
            return {"success": False, "message": f"Error al registrar entrada: {e}"}

    @staticmethod
    def register_exit(spare_part_id: str, quantity: int, motive: str, note: str,
                      user_id: str, work_order_id: str = None,
                      attachment_file=None, upload_folder: str = None) -> Dict:
        if not spare_part_id:
            return {"success": False, "message": "Debe seleccionar un repuesto"}
        if quantity <= 0:
            return {"success": False, "message": "La cantidad debe ser mayor a cero"}
        if motive not in StockMovementModel.EXIT_MOTIVES:
            return {"success": False, "message": "Motivo de salida inválido"}
        try:
            part = SparePartRepository.find_by_id(spare_part_id)
            if not part:
                return {"success": False, "message": "Repuesto no encontrado"}
            if part.stock_actual < quantity:
                return {"success": False, "message": f"Stock insuficiente. Stock actual: {part.stock_actual}"}
            attachment_path = _save_attachment(attachment_file, upload_folder,
                                               f"salida_{spare_part_id}") if upload_folder else None
            new_stock = part.stock_actual - quantity
            SparePartRepository.update_stock(spare_part_id, new_stock)
            movement = StockMovementModel(
                spare_part_id=spare_part_id,
                movement_type="salida",
                quantity=quantity,
                motive=motive,
                note=note.strip() if note else None,
                user_id=user_id,
                work_order_id=work_order_id,
                attachment_path=attachment_path
            )
            StockMovementRepository.create(movement)
            return {"success": True, "message": f"Salida registrada. Nuevo stock: {new_stock}"}
        except Exception as e:
            return {"success": False, "message": f"Error al registrar salida: {e}"}

    @staticmethod
    def get_movements_by_part(spare_part_id: str) -> Dict:
        try:
            movements = StockMovementRepository.find_by_spare_part(spare_part_id)
            return {"success": True, "movements": movements}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener movimientos: {e}"}

    @staticmethod
    def get_all_for_report(spare_part_id: str = None, movement_type: str = None,
                           start_date_str: str = None, end_date_str: str = None) -> Dict:
        try:
            start_date = None
            end_date = None
            if start_date_str:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
            if end_date_str:
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            movements = StockMovementRepository.find_all_filtered(
                spare_part_id, movement_type, start_date, end_date
            )
            return {"success": True, "movements": movements}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener movimientos para reporte: {e}"}
