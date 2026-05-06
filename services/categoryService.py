from typing import Dict
from models.categoryModel import CategoryModel
from repositories.categoryRepository import CategoryRepository
from repositories.sparePartRepository import SparePartRepository

class CategoryService:

    @staticmethod
    def get_all() -> Dict:
        try:
            categories = CategoryRepository.find_all()
            return {"success": True, "categories": categories}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener categorías: {e}"}

    @staticmethod
    def get_by_id(category_id: str) -> Dict:
        try:
            category = CategoryRepository.find_by_id(category_id)
            if not category:
                return {"success": False, "message": "Categoría no encontrada"}
            return {"success": True, "category": category}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener la categoría: {e}"}

    @staticmethod
    def create(name: str, description: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        name = name.strip()
        try:
            if CategoryRepository.exist_by_name(name):
                return {"success": False, "message": "Ya existe una categoría con ese nombre"}
            category = CategoryModel(name=name, description=description.strip() if description else None)
            CategoryRepository.create(category)
            return {"success": True, "message": "Categoría creada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al crear la categoría: {e}"}

    @staticmethod
    def update(category_id: str, name: str, description: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        name = name.strip()
        try:
            if not CategoryRepository.find_by_id(category_id):
                return {"success": False, "message": "Categoría no encontrada"}
            if CategoryRepository.exist_by_name(name, exclude_id=category_id):
                return {"success": False, "message": "Ya existe una categoría con ese nombre"}
            CategoryRepository.update_by_id(category_id, {
                "name": name,
                "description": description.strip() if description else None
            })
            return {"success": True, "message": "Categoría actualizada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar la categoría: {e}"}

    @staticmethod
    def delete(category_id: str) -> Dict:
        try:
            if not CategoryRepository.find_by_id(category_id):
                return {"success": False, "message": "Categoría no encontrada"}
            parts, _ = SparePartRepository.find_paginated(1, 1, category_id=category_id)
            if parts:
                return {"success": False, "message": "No se puede eliminar: hay repuestos vinculados a esta categoría"}
            CategoryRepository.delete_by_id(category_id)
            return {"success": True, "message": "Categoría eliminada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar la categoría: {e}"}
