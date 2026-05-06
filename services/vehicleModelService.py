from typing import Dict
from models.vehicleModelModel import VehicleModelModel
from repositories.vehicleModelRepository import VehicleModelRepository
from repositories.sparePartRepository import SparePartRepository

class VehicleModelService:

    @staticmethod
    def get_all() -> Dict:
        try:
            models = VehicleModelRepository.find_all()
            return {"success": True, "vehicle_models": models}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener modelos: {e}"}

    @staticmethod
    def get_by_brand(brand_id: str) -> Dict:
        try:
            models = VehicleModelRepository.find_by_brand(brand_id)
            return {"success": True, "vehicle_models": models}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener modelos por marca: {e}"}

    @staticmethod
    def get_by_id(vm_id: str) -> Dict:
        try:
            vm = VehicleModelRepository.find_by_id(vm_id)
            if not vm:
                return {"success": False, "message": "Modelo no encontrado"}
            return {"success": True, "vehicle_model": vm}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener el modelo: {e}"}

    @staticmethod
    def create(name: str, description: str, brand_id: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        name = name.strip()
        brand_id = brand_id.strip() if brand_id else None
        try:
            if VehicleModelRepository.exist_by_name(name, brand_id=brand_id):
                return {"success": False, "message": "Ya existe un modelo con ese nombre para esta marca"}
            VehicleModelRepository.create(VehicleModelModel(
                name=name,
                description=description.strip() if description else None,
                brand_id=brand_id
            ))
            return {"success": True, "message": "Modelo creado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al crear el modelo: {e}"}

    @staticmethod
    def update(vm_id: str, name: str, description: str, brand_id: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        name = name.strip()
        brand_id = brand_id.strip() if brand_id else None
        try:
            if not VehicleModelRepository.find_by_id(vm_id):
                return {"success": False, "message": "Modelo no encontrado"}
            if VehicleModelRepository.exist_by_name(name, brand_id=brand_id, exclude_id=vm_id):
                return {"success": False, "message": "Ya existe un modelo con ese nombre para esta marca"}
            VehicleModelRepository.update_by_id(vm_id, {
                "name": name,
                "description": description.strip() if description else None,
                "brand_id": brand_id
            })
            return {"success": True, "message": "Modelo actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar el modelo: {e}"}

    @staticmethod
    def delete(vm_id: str) -> Dict:
        try:
            if not VehicleModelRepository.find_by_id(vm_id):
                return {"success": False, "message": "Modelo no encontrado"}
            parts, _ = SparePartRepository.find_paginated(1, 1, vehicle_model_id=vm_id)
            if parts:
                return {"success": False, "message": "No se puede eliminar: hay repuestos vinculados a este modelo"}
            VehicleModelRepository.delete_by_id(vm_id)
            return {"success": True, "message": "Modelo eliminado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar el modelo: {e}"}
