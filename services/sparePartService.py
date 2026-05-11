from typing import Dict
import os
from werkzeug.utils import secure_filename
from models.sparePartModel import SparePartModel
from repositories.sparePartRepository import SparePartRepository
from repositories.stockMovementRepository import StockMovementRepository

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

class SparePartService:

    @staticmethod
    def get_paginated(page: int = 1, per_page: int = 10, search: str = None,
                      category_id: str = None, brand_id: str = None, vehicle_model_id: str = None) -> Dict:
        try:
            parts, total = SparePartRepository.find_paginated(
                page, per_page, search, category_id, brand_id, vehicle_model_id)
            total_pages = max(1, (total + per_page - 1) // per_page)
            return {"success": True, "parts": parts, "total": total, "page": page,
                    "per_page": per_page, "total_pages": total_pages}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener repuestos: {e}"}

    @staticmethod
    def get_all_active() -> Dict:
        try:
            parts = SparePartRepository.find_all_active()
            return {"success": True, "parts": parts}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener repuestos: {e}"}

    @staticmethod
    def get_by_id(part_id: str) -> Dict:
        try:
            part = SparePartRepository.find_by_id(part_id)
            if not part:
                return {"success": False, "message": "Repuesto no encontrado"}
            return {"success": True, "part": part}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener el repuesto: {e}"}

    @staticmethod
    def create(data: dict, imagen_file=None, upload_folder: str = None) -> Dict:
        code = data.get("code", "").strip()
        name = data.get("name", "").strip()
        if not name:
            return {"success": False, "message": "El nombre es obligatorio"}
        try:
            if not code:
                code = SparePartRepository.get_next_code()
            if SparePartRepository.exist_by_code(code):
                return {"success": False, "message": "Ya existe un repuesto con ese código"}

            imagen_path = None
            if imagen_file and imagen_file.filename and _allowed_file(imagen_file.filename):
                filename = secure_filename(f"{code}_{imagen_file.filename}")
                save_path = os.path.join(upload_folder, filename)
                imagen_file.save(save_path)
                imagen_path = f"uploads/repuestos/{filename}"

            part = SparePartModel(
                code=code,
                name=name,
                description=data.get("description", "").strip() or None,
                brand_id=data.get("brand_id") or None,
                vehicle_model_id=data.get("vehicle_model_id") or None,
                category_id=data.get("category_id") or None,
                supplier_id=data.get("supplier_id") or None,
                stock_actual=int(data.get("stock_actual", 0)),
                stock_minimo=int(data.get("stock_minimo", 0)),
                stock_maximo=int(data.get("stock_maximo", 0)),
                precio_compra=float(data.get("precio_compra", 0.0)),
                precio_venta=float(data.get("precio_venta", 0.0)),
                ubicacion=data.get("ubicacion", "").strip() or None,
                imagen=imagen_path
            )
            SparePartRepository.create(part)
            return {"success": True, "message": "Repuesto creado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al crear el repuesto: {e}"}

    @staticmethod
    def update(part_id: str, data: dict, imagen_file=None, upload_folder: str = None) -> Dict:
        code = data.get("code", "").strip()
        name = data.get("name", "").strip()
        if not code:
            return {"success": False, "message": "El código es obligatorio"}
        if not name:
            return {"success": False, "message": "El nombre es obligatorio"}
        try:
            part = SparePartRepository.find_by_id(part_id)
            if not part:
                return {"success": False, "message": "Repuesto no encontrado"}
            if SparePartRepository.exist_by_code(code, exclude_id=part_id):
                return {"success": False, "message": "Ya existe un repuesto con ese código"}

            update_data = {
                "code": code,
                "name": name,
                "description": data.get("description", "").strip() or None,
                "brand_id": data.get("brand_id") or None,
                "vehicle_model_id": data.get("vehicle_model_id") or None,
                "category_id": data.get("category_id") or None,
                "supplier_id": data.get("supplier_id") or None,
                "stock_minimo": int(data.get("stock_minimo", 0)),
                "stock_maximo": int(data.get("stock_maximo", 0)),
                "precio_compra": float(data.get("precio_compra", 0.0)),
                "precio_venta": float(data.get("precio_venta", 0.0)),
                "ubicacion": data.get("ubicacion", "").strip() or None
            }

            if imagen_file and imagen_file.filename and _allowed_file(imagen_file.filename):
                filename = secure_filename(f"{code}_{imagen_file.filename}")
                save_path = os.path.join(upload_folder, filename)
                imagen_file.save(save_path)
                update_data["imagen"] = f"uploads/repuestos/{filename}"

            SparePartRepository.update_by_id(part_id, update_data)
            return {"success": True, "message": "Repuesto actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar el repuesto: {e}"}

    @staticmethod
    def delete(part_id: str) -> Dict:
        try:
            part = SparePartRepository.find_by_id(part_id)
            if not part:
                return {"success": False, "message": "Repuesto no encontrado"}
            if StockMovementRepository.has_movements_for_part(part_id):
                return {"success": False, "message": "No se puede eliminar: el repuesto tiene movimientos de stock registrados. Puedes desactivarlo en su lugar."}
            SparePartRepository.delete_by_id(part_id)
            return {"success": True, "message": "Repuesto eliminado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar el repuesto: {e}"}

    @staticmethod
    def deactivate(part_id: str) -> Dict:
        try:
            if not SparePartRepository.find_by_id(part_id):
                return {"success": False, "message": "Repuesto no encontrado"}
            SparePartRepository.update_by_id(part_id, {"is_active": False})
            return {"success": True, "message": "Repuesto desactivado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al desactivar el repuesto: {e}"}

    @staticmethod
    def get_critical_stock() -> Dict:
        try:
            parts = SparePartRepository.find_critical_stock()
            return {"success": True, "parts": parts}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener stock crítico: {e}"}
