from typing import Dict
from models.brandModel import BrandModel
from repositories.brandRepository import BrandRepository
from repositories.sparePartRepository import SparePartRepository

class BrandService:

    @staticmethod
    def get_all() -> Dict:
        try:
            brands = BrandRepository.find_all()
            return {"success": True, "brands": brands}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener marcas: {e}"}

    @staticmethod
    def get_by_id(brand_id: str) -> Dict:
        try:
            brand = BrandRepository.find_by_id(brand_id)
            if not brand:
                return {"success": False, "message": "Marca no encontrada"}
            return {"success": True, "brand": brand}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener la marca: {e}"}

    @staticmethod
    def create(name: str, description: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        name = name.strip()
        try:
            if BrandRepository.exist_by_name(name):
                return {"success": False, "message": "Ya existe una marca con ese nombre"}
            BrandRepository.create(BrandModel(name=name, description=description.strip() if description else None))
            return {"success": True, "message": "Marca creada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al crear la marca: {e}"}

    @staticmethod
    def update(brand_id: str, name: str, description: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        name = name.strip()
        try:
            if not BrandRepository.find_by_id(brand_id):
                return {"success": False, "message": "Marca no encontrada"}
            if BrandRepository.exist_by_name(name, exclude_id=brand_id):
                return {"success": False, "message": "Ya existe una marca con ese nombre"}
            BrandRepository.update_by_id(brand_id, {
                "name": name,
                "description": description.strip() if description else None
            })
            return {"success": True, "message": "Marca actualizada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar la marca: {e}"}

    @staticmethod
    def delete(brand_id: str) -> Dict:
        try:
            if not BrandRepository.find_by_id(brand_id):
                return {"success": False, "message": "Marca no encontrada"}
            parts, _ = SparePartRepository.find_paginated(1, 1, brand_id=brand_id)
            if parts:
                return {"success": False, "message": "No se puede eliminar: hay repuestos vinculados a esta marca"}
            BrandRepository.delete_by_id(brand_id)
            return {"success": True, "message": "Marca eliminada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar la marca: {e}"}
