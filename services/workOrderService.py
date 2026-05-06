import json
from typing import Dict
from datetime import datetime
from models.workOrderModel import WorkOrderModel
from repositories.workOrderRepository import WorkOrderRepository
from repositories.sparePartRepository import SparePartRepository
from services.stockService import StockService

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
    def get_by_client(client_id: str) -> Dict:
        try:
            orders = WorkOrderRepository.find_by_client(client_id)
            return {"success": True, "orders": orders}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener órdenes del cliente: {e}"}

    @staticmethod
    def create(data: dict, parts_json: str, operator_id: str) -> Dict:
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
                status="abierta",
                operator_id=operator_id,
                notes=data.get("notes", "").strip() or None
            )
            order_id = WorkOrderRepository.create(order)
            return {"success": True, "message": "Orden de trabajo creada exitosamente", "order_id": order_id}
        except Exception as e:
            return {"success": False, "message": f"Error al crear la orden: {e}"}

    @staticmethod
    def update(order_id: str, data: dict, parts_json: str) -> Dict:
        try:
            order = WorkOrderRepository.find_by_id(order_id)
            if not order:
                return {"success": False, "message": "Orden no encontrada"}
            if order.status == "cerrada":
                return {"success": False, "message": "No se puede editar una orden cerrada"}

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

            update_data = {
                "vehicle_brand": data.get("vehicle_brand", order.vehicle_brand).strip(),
                "vehicle_model": data.get("vehicle_model", order.vehicle_model).strip(),
                "vehicle_plate": data.get("vehicle_plate", order.vehicle_plate).strip().upper(),
                "client_id": data.get("client_id", order.client_id),
                "parts": parts,
                "labor_cost": labor_cost,
                "total": total,
                "status": new_status,
                "notes": data.get("notes", "").strip() or None,
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
            if order.status == "cerrada":
                return {"success": False, "message": "La orden ya está cerrada"}

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

            WorkOrderRepository.update_by_id(order_id, {"status": "cerrada", "updated_at": datetime.now()})
            return {"success": True, "message": "Orden cerrada y stock descontado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al cerrar la orden: {e}"}
