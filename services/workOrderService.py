import json
import os
from typing import Dict, List
from datetime import datetime
from werkzeug.utils import secure_filename
from models.workOrderModel import WorkOrderModel
from repositories.workOrderRepository import WorkOrderRepository
from repositories.sparePartRepository import SparePartRepository
from services.stockService import StockService

ALLOWED_PHOTO_EXT = {"png", "jpg", "jpeg", "gif", "webp"}

def _allowed_photo(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_PHOTO_EXT

class WorkOrderService:

    @staticmethod
    def get_paginated(page: int = 1, per_page: int = 10, search: str = None,
                      status: str = None, client_id: str = None) -> Dict:
        try:
            orders, total = WorkOrderRepository.find_paginated(page, per_page, search, status, client_id)
            total_pages = max(1, (total + per_page - 1) // per_page)
            return {"success": True, "orders": orders, "total": total,
                    "page": page, "per_page": per_page, "total_pages": total_pages}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener órdenes: {e}"}

    @staticmethod
    def get_by_id(order_id: str) -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Orden de trabajo no encontrada"}
            return {"success": True, "order": order}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener la orden: {e}"}

    @staticmethod
    def get_by_mechanic(mechanic_id: str) -> Dict:
        try:
            orders = WorkOrderRepository.find_by_mechanic(mechanic_id)
            return {"success": True, "orders": orders}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener órdenes del mecánico: {e}"}

    @staticmethod
    def get_by_client(client_id: str) -> Dict:
        try:
            orders = WorkOrderRepository.find_by_client(client_id)
            return {"success": True, "orders": orders}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener órdenes del cliente: {e}"}

    @staticmethod
    def create(data: dict, parts_json: str, operator_id: str,
               photo_files=None, upload_folder: str = None) -> Dict:
        client_id = data.get("client_id", "").strip()
        vehicle_brand = data.get("vehicle_brand", "").strip()
        vehicle_model = data.get("vehicle_model", "").strip()
        vehicle_plate = data.get("vehicle_plate", "").strip()

        if not client_id:
            return {"success": False, "message": "Debe seleccionar un cliente"}
        if not vehicle_brand:
            return {"success": False, "message": "La marca del vehículo es obligatoria"}
        if not vehicle_model:
            return {"success": False, "message": "El modelo del vehículo es obligatorio"}
        if not vehicle_plate:
            return {"success": False, "message": "La placa del vehículo es obligatoria"}

        try:
            parts = json.loads(parts_json) if parts_json else []
        except Exception:
            parts = []

        try:
            labor_cost = float(data.get("labor_cost", 0.0))
        except (ValueError, TypeError):
            labor_cost = 0.0

        subtotal = sum(float(p.get("subtotal", 0)) for p in parts)
        total = subtotal + labor_cost

        vehicle_photos = []
        if photo_files and upload_folder:
            os.makedirs(upload_folder, exist_ok=True)
            for photo in photo_files:
                if photo and photo.filename and _allowed_photo(photo.filename):
                    filename = secure_filename(f"{vehicle_plate}_{photo.filename}")
                    photo.save(os.path.join(upload_folder, filename))
                    vehicle_photos.append(f"uploads/ordenes/{filename}")

        try:
            number = WorkOrderRepository.get_next_number()
            order = WorkOrderModel(
                number=number,
                client_id=client_id,
                vehicle_brand=vehicle_brand,
                vehicle_model=vehicle_model,
                vehicle_plate=vehicle_plate.upper(),
                parts=parts,
                labor_cost=labor_cost,
                total=total,
                status="ingresado",
                operator_id=operator_id,
                mechanic_id=data.get("mechanic_id") or None,
                notes=data.get("notes", "").strip() or None,
                vehicle_photos=vehicle_photos
            )
            order_id = WorkOrderRepository.create(order)
            return {"success": True, "message": "Orden de trabajo creada exitosamente", "order_id": order_id}
        except Exception as e:
            return {"success": False, "message": f"Error al crear la orden: {e}"}

    @staticmethod
    def update(order_id: str, data: dict, parts_json: str,
               photo_files=None, upload_folder: str = None) -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Orden no encontrada"}
            if order.is_closed:
                return {"success": False, "message": "No se puede editar una orden finalizada"}

            try:
                parts = json.loads(parts_json) if parts_json else []
            except Exception:
                parts = []

            try:
                labor_cost = float(data.get("labor_cost", 0.0))
            except (ValueError, TypeError):
                labor_cost = 0.0

            subtotal = sum(float(p.get("subtotal", 0)) for p in parts)
            total = subtotal + labor_cost

            new_status = data.get("status", order.status)
            if new_status not in WorkOrderModel.VALID_STATUSES:
                new_status = order.status

            vehicle_photos = list(order.vehicle_photos)
            if photo_files and upload_folder:
                os.makedirs(upload_folder, exist_ok=True)
                plate = data.get("vehicle_plate", order.vehicle_plate).strip().upper()
                for photo in photo_files:
                    if photo and photo.filename and _allowed_photo(photo.filename):
                        filename = secure_filename(f"{plate}_{photo.filename}")
                        photo.save(os.path.join(upload_folder, filename))
                        vehicle_photos.append(f"uploads/ordenes/{filename}")

            update_data = {
                "vehicle_brand": data.get("vehicle_brand", order.vehicle_brand).strip(),
                "vehicle_model": data.get("vehicle_model", order.vehicle_model).strip(),
                "vehicle_plate": data.get("vehicle_plate", order.vehicle_plate).strip().upper(),
                "client_id": data.get("client_id", order.client_id),
                "mechanic_id": data.get("mechanic_id") or None,
                "parts": parts,
                "labor_cost": labor_cost,
                "total": total,
                "status": new_status,
                "notes": data.get("notes", "").strip() or None,
                "vehicle_photos": vehicle_photos,
                "updated_at": datetime.now()
            }
            WorkOrderRepository.update_by_id(order_id, update_data)
            return {"success": True, "message": "Orden actualizada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar la orden: {e}"}

    @staticmethod
    def close_order(order_id: str, user_id: str) -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Orden no encontrada"}
            if order.is_closed:
                return {"success": False, "message": "La orden ya está finalizada"}

            # Validar stock antes de descontar
            for part in order.parts:
                part_obj = SparePartRepository.find_by_id(part["spare_part_id"])
                if not part_obj:
                    return {"success": False, "message": f"Repuesto '{part.get('spare_part_name', '')}' no encontrado"}
                if part_obj.stock_actual < int(part["quantity"]):
                    return {"success": False,
                            "message": f"Stock insuficiente para '{part_obj.name}'. Stock actual: {part_obj.stock_actual}"}

            # Descontar stock y registrar movimientos
            for part in order.parts:
                result = StockService.register_exit(
                    spare_part_id=part["spare_part_id"],
                    quantity=int(part["quantity"]),
                    motive="orden_trabajo",
                    note=f"Orden #{order.number}",
                    user_id=user_id,
                    work_order_id=order_id
                )
                if not result["success"]:
                    return {"success": False, "message": result["message"]}

            WorkOrderRepository.update_by_id(order_id, {"status": "finalizado", "updated_at": datetime.now()})
            return {"success": True, "message": "Orden finalizada y stock descontado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al cerrar la orden: {e}"}
