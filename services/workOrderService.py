import json
import os
from typing import Dict
from datetime import datetime
from werkzeug.utils import secure_filename
from models.workOrderModel import WorkOrderModel, _LEGACY_MAP
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
            return {"success": False, "message": f"Error al obtener ingresos: {e}"}

    @staticmethod
    def get_by_id(order_id: str) -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Ingreso no encontrado"}
            return {"success": True, "order": order}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener el ingreso: {e}"}

    @staticmethod
    def get_by_mechanic(mechanic_id: str) -> Dict:
        try:
            orders = WorkOrderRepository.find_by_mechanic(mechanic_id)
            return {"success": True, "orders": orders}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener ingresos del mecánico: {e}"}

    @staticmethod
    def get_by_client(client_id: str) -> Dict:
        try:
            orders = WorkOrderRepository.find_by_client(client_id)
            return {"success": True, "orders": orders}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener ingresos del cliente: {e}"}

    @staticmethod
    def create(data: dict, parts_json: str, operator_id: str,
               photo_files=None, upload_folder: str = None) -> Dict:
        client_id = data.get("client_id", "").strip()
        vehicle_brand = data.get("vehicle_brand", "").strip()
        vehicle_model = data.get("vehicle_model", "").strip()
        vehicle_plate = data.get("vehicle_plate", "").strip()
        vehicle_year = data.get("vehicle_year", "").strip() or None

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
                vehicle_year=vehicle_year,
                parts=parts,
                labor_cost=labor_cost,
                total=total,
                status="recepcion",
                operator_id=operator_id,
                mechanic_id=data.get("mechanic_id") or None,
                notes=data.get("notes", "").strip() or None,
                vehicle_photos=vehicle_photos
            )
            order_id = WorkOrderRepository.create(order)
            return {"success": True, "message": "Ingreso creado exitosamente", "order_id": order_id}
        except Exception as e:
            return {"success": False, "message": f"Error al crear el ingreso: {e}"}

    @staticmethod
    def update(order_id: str, data: dict, parts_json: str,
               photo_files=None, upload_folder: str = None) -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Ingreso no encontrado"}
            if order.is_closed:
                return {"success": False, "message": "No se puede editar un ingreso ya entregado"}

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
                "vehicle_year": data.get("vehicle_year", "").strip() or order.vehicle_year or None,
                "client_id": data.get("client_id") or order.client_id,
                "mechanic_id": data.get("mechanic_id") or None,
                "parts": parts,
                "labor_cost": labor_cost,
                "total": total,
                "notes": data.get("notes", "").strip() or None,
                "vehicle_photos": vehicle_photos,
                "updated_at": datetime.now()
            }
            WorkOrderRepository.update_by_id(order_id, update_data)
            return {"success": True, "message": "Ingreso actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar el ingreso: {e}"}

    @staticmethod
    def advance_status(order_id: str, user_role: str, user_id: str,
                       user_name: str = "", reason: str = "") -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Ingreso no encontrado"}

            # Normalize legacy status
            current = _LEGACY_MAP.get(order.status, order.status)
            flow = WorkOrderModel.STATUS_FLOW

            if current not in flow:
                current = "recepcion"

            idx = flow.index(current)
            if idx >= len(flow) - 1:
                return {"success": False, "message": "Este ingreso ya fue entregado"}

            next_status = flow[idx + 1]

            # Permission check
            allowed = WorkOrderModel.STATUS_TRANSITIONS.get(current, [])
            if user_role not in allowed:
                return {"success": False,
                        "message": f"Tu rol no puede avanzar desde '{WorkOrderModel.STATUS_LABELS[current]}'"}

            # Client can only approve their own order
            if user_role == "client" and order.client_id != user_id:
                return {"success": False, "message": "No tienes permiso para aprobar este presupuesto"}

            # Admin/operator must provide reason only for final delivery step
            if user_role in ("admin", "operator") and current == "pago_pendiente" and not reason.strip():
                return {"success": False,
                        "message": "Debe indicar el número de comprobante o referencia de pago"}

            # Diagnostico → presupuesto requires parts or labor
            if current == "diagnostico" and next_status == "presupuesto":
                if not order.parts and order.labor_cost <= 0:
                    return {"success": False,
                            "message": "Debe registrar repuestos o mano de obra antes de emitir el presupuesto"}

            # Stock deduction on delivery
            if next_status == "entregado":
                for part in order.parts:
                    part_obj = SparePartRepository.find_by_id(part["spare_part_id"])
                    if not part_obj:
                        return {"success": False,
                                "message": f"Repuesto '{part.get('spare_part_name', '')}' no encontrado"}
                    if part_obj.stock_actual < int(part["quantity"]):
                        return {"success": False,
                                "message": (f"Stock insuficiente para '{part_obj.name}'. "
                                            f"Disponible: {part_obj.stock_actual}, requerido: {part['quantity']}")}

                for part in order.parts:
                    result = StockService.register_exit(
                        spare_part_id=part["spare_part_id"],
                        quantity=int(part["quantity"]),
                        motive="orden_trabajo",
                        note=f"Ingreso #{order.number}",
                        user_id=user_id,
                        work_order_id=order_id
                    )
                    if not result["success"]:
                        return {"success": False, "message": result["message"]}

            history_entry = {
                "action": "advance",
                "from_status": current,
                "to_status": next_status,
                "user_id": user_id,
                "user_name": user_name,
                "reason": reason.strip(),
                "timestamp": datetime.now()
            }
            WorkOrderRepository.update_by_id(order_id, {
                "status": next_status,
                "status_history": order.status_history + [history_entry],
                "updated_at": datetime.now()
            })
            label = WorkOrderModel.STATUS_LABELS[next_status]
            return {"success": True, "message": f"Estado actualizado: {label}", "new_status": next_status}
        except Exception as e:
            return {"success": False, "message": f"Error al avanzar el estado: {e}"}

    @staticmethod
    def update_mechanic_work(order_id: str, user_id: str, user_role: str,
                              parts_json: str, labor_cost_str: str, notes: str,
                              photo_files=None, upload_folder: str = None) -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Ingreso no encontrado"}
            if user_role == "mechanic" and order.mechanic_id != user_id:
                return {"success": False, "message": "No eres el mecánico asignado a este ingreso"}
            if order.canonical_status not in ("diagnostico", "en_reparacion"):
                return {"success": False,
                        "message": "Solo puedes registrar trabajo en Diagnóstico o En Reparación"}

            try:
                parts = json.loads(parts_json) if parts_json else []
            except Exception:
                parts = []

            try:
                labor_cost = float(labor_cost_str or 0)
            except (ValueError, TypeError):
                labor_cost = 0.0

            subtotal = sum(float(p.get("subtotal", 0)) for p in parts)
            total = subtotal + labor_cost

            work_photos = list(order.work_photos)
            if photo_files and upload_folder:
                os.makedirs(upload_folder, exist_ok=True)
                for photo in photo_files:
                    if photo and photo.filename and _allowed_photo(photo.filename):
                        filename = secure_filename(f"work_{order.vehicle_plate}_{photo.filename}")
                        photo.save(os.path.join(upload_folder, filename))
                        work_photos.append(f"uploads/ordenes/{filename}")

            WorkOrderRepository.update_by_id(order_id, {
                "parts": parts,
                "labor_cost": labor_cost,
                "total": total,
                "work_notes": notes.strip() if notes else order.work_notes,
                "work_photos": work_photos,
                "updated_at": datetime.now()
            })
            return {"success": True, "message": "Trabajo registrado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al registrar el trabajo: {e}"}

    @staticmethod
    def revert_status(order_id: str, user_role: str, user_id: str,
                      user_name: str = "", reason: str = "") -> Dict:
        try:
            if not reason.strip():
                return {"success": False, "message": "Debe indicar el motivo del retroceso de estado"}

            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Ingreso no encontrado"}

            if not order.can_user_revert(user_role):
                return {"success": False, "message": "No tienes permiso para retroceder este ingreso"}

            current = order.canonical_status
            flow = WorkOrderModel.STATUS_FLOW
            idx = flow.index(current)
            prev = flow[idx - 1]

            history_entry = {
                "action": "revert",
                "from_status": current,
                "to_status": prev,
                "user_id": user_id,
                "user_name": user_name,
                "reason": reason.strip(),
                "timestamp": datetime.now()
            }
            WorkOrderRepository.update_by_id(order_id, {
                "status": prev,
                "status_history": order.status_history + [history_entry],
                "updated_at": datetime.now()
            })
            label = WorkOrderModel.STATUS_LABELS[prev]
            return {"success": True, "message": f"Estado revertido a: {label}"}
        except Exception as e:
            return {"success": False, "message": f"Error al revertir el estado: {e}"}

    @staticmethod
    def upload_payment_proof(order_id: str, user_id: str, user_role: str,
                             proof_file, upload_folder: str) -> Dict:
        ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp", "pdf"}
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Ingreso no encontrado"}

            if order.canonical_status != "pago_pendiente":
                return {"success": False,
                        "message": "Solo se puede subir el comprobante en estado Pago Pendiente"}

            if user_role == "client" and order.client_id != user_id:
                return {"success": False, "message": "No tienes permiso para subir el comprobante"}

            if not proof_file or not proof_file.filename:
                return {"success": False, "message": "Debe seleccionar un archivo"}

            ext = proof_file.filename.rsplit(".", 1)[-1].lower() if "." in proof_file.filename else ""
            if ext not in ALLOWED_EXT:
                return {"success": False, "message": "Formato no permitido. Use imagen (JPG, PNG) o PDF"}

            os.makedirs(upload_folder, exist_ok=True)
            filename = secure_filename(f"comprobante_{order.number}.{ext}")
            proof_file.save(os.path.join(upload_folder, filename))
            proof_path = f"uploads/ordenes/{filename}"

            WorkOrderRepository.update_by_id(order_id, {
                "payment_proof_path": proof_path,
                "updated_at": datetime.now()
            })
            return {"success": True, "message": "Comprobante de pago subido correctamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al subir el comprobante: {e}"}
