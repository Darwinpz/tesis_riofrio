from typing import Dict
from models.serviceModel import ServiceModel
from repositories.serviceRepository import ServiceRepository

class ServiceService:

    @staticmethod
    def get_all() -> Dict:
        try:
            services = ServiceRepository.find_all()
            return {"success": True, "services": services}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener servicios: {e}"}

    @staticmethod
    def get_all_active() -> Dict:
        try:
            services = ServiceRepository.find_all_active()
            return {"success": True, "services": services}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener servicios: {e}"}

    @staticmethod
    def get_by_id(service_id: str) -> Dict:
        try:
            svc = ServiceRepository.find_by_id(service_id)
            if not svc:
                return {"success": False, "message": "Servicio no encontrado"}
            return {"success": True, "service": svc}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener el servicio: {e}"}

    @staticmethod
    def create(data: dict) -> Dict:
        name = data.get("name", "").strip()
        if not name:
            return {"success": False, "message": "El nombre del servicio es obligatorio"}
        try:
            price = float(data.get("price", 0.0))
        except (ValueError, TypeError):
            price = 0.0
        try:
            if ServiceRepository.exist_by_name(name):
                return {"success": False, "message": "Ya existe un servicio con ese nombre"}
            svc = ServiceModel(
                name=name,
                description=data.get("description", "").strip() or None,
                price=price
            )
            ServiceRepository.create(svc)
            return {"success": True, "message": "Servicio creado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al crear el servicio: {e}"}

    @staticmethod
    def update(service_id: str, data: dict) -> Dict:
        name = data.get("name", "").strip()
        if not name:
            return {"success": False, "message": "El nombre del servicio es obligatorio"}
        try:
            price = float(data.get("price", 0.0))
        except (ValueError, TypeError):
            price = 0.0
        try:
            if not ServiceRepository.find_by_id(service_id):
                return {"success": False, "message": "Servicio no encontrado"}
            if ServiceRepository.exist_by_name(name, exclude_id=service_id):
                return {"success": False, "message": "Ya existe un servicio con ese nombre"}
            ServiceRepository.update_by_id(service_id, {
                "name": name,
                "description": data.get("description", "").strip() or None,
                "price": price
            })
            return {"success": True, "message": "Servicio actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar el servicio: {e}"}

    @staticmethod
    def delete(service_id: str) -> Dict:
        try:
            if not ServiceRepository.find_by_id(service_id):
                return {"success": False, "message": "Servicio no encontrado"}
            ServiceRepository.delete_by_id(service_id)
            return {"success": True, "message": "Servicio eliminado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar el servicio: {e}"}
