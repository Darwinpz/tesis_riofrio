from typing import Dict
from models.supplierModel import SupplierModel
from repositories.supplierRepository import SupplierRepository
from repositories.sparePartRepository import SparePartRepository

class SupplierService:

    @staticmethod
    def get_all() -> Dict:
        try:
            suppliers = SupplierRepository.find_all()
            return {"success": True, "suppliers": suppliers}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener proveedores: {e}"}

    @staticmethod
    def get_by_id(supplier_id: str) -> Dict:
        try:
            supplier = SupplierRepository.find_by_id(supplier_id)
            if not supplier:
                return {"success": False, "message": "Proveedor no encontrado"}
            return {"success": True, "supplier": supplier}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener el proveedor: {e}"}

    @staticmethod
    def create(name: str, contact: str, phone: str, email: str, address: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        try:
            supplier = SupplierModel(
                name=name.strip(),
                contact=contact.strip() if contact else None,
                phone=phone.strip() if phone else None,
                email=email.strip() if email else None,
                address=address.strip() if address else None
            )
            SupplierRepository.create(supplier)
            return {"success": True, "message": "Proveedor creado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al crear el proveedor: {e}"}

    @staticmethod
    def update(supplier_id: str, name: str, contact: str, phone: str, email: str, address: str) -> Dict:
        if not name or not name.strip():
            return {"success": False, "message": "El nombre es obligatorio"}
        try:
            if not SupplierRepository.find_by_id(supplier_id):
                return {"success": False, "message": "Proveedor no encontrado"}
            SupplierRepository.update_by_id(supplier_id, {
                "name": name.strip(),
                "contact": contact.strip() if contact else None,
                "phone": phone.strip() if phone else None,
                "email": email.strip() if email else None,
                "address": address.strip() if address else None
            })
            return {"success": True, "message": "Proveedor actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar el proveedor: {e}"}

    @staticmethod
    def delete(supplier_id: str) -> Dict:
        try:
            if not SupplierRepository.find_by_id(supplier_id):
                return {"success": False, "message": "Proveedor no encontrado"}
            # Verificar que no haya repuestos vinculados
            all_parts = SparePartRepository.find_all_active()
            if any(p.supplier_id == supplier_id for p in all_parts):
                return {"success": False, "message": "No se puede eliminar: hay repuestos vinculados a este proveedor"}
            SupplierRepository.delete_by_id(supplier_id)
            return {"success": True, "message": "Proveedor eliminado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar el proveedor: {e}"}
