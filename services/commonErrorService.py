from typing import Dict
from models.commonErrorModel import CommonErrorModel
from repositories.commonErrorRepository import CommonErrorRepository


class CommonErrorService:

    @staticmethod
    def get_all(brand_id: str = None, vehicle_model_id: str = None) -> Dict:
        try:
            errors = CommonErrorRepository.find_all(brand_id, vehicle_model_id)
            return {"success": True, "errors": errors}
        except Exception as e:
            return {"success": False, "message": str(e), "errors": []}

    @staticmethod
    def get_by_id(error_id: str) -> Dict:
        try:
            error = CommonErrorRepository.find_by_id(error_id)
            if not error:
                return {"success": False, "message": "Error no encontrado"}
            return {"success": True, "error": error}
        except Exception as e:
            return {"success": False, "message": str(e)}

    @staticmethod
    def create(brand_id: str, vehicle_model_id: str, year_from, year_to,
               title: str, description: str, severity: str) -> Dict:
        if not title or not title.strip():
            return {"success": False, "message": "El título es obligatorio"}
        if severity not in CommonErrorModel.SEVERITIES:
            severity = "media"
        try:
            year_from_int = int(year_from) if year_from else None
            year_to_int = int(year_to) if year_to else None
        except (ValueError, TypeError):
            return {"success": False, "message": "El año debe ser un número válido"}
        try:
            error = CommonErrorModel(
                brand_id=brand_id or None,
                vehicle_model_id=vehicle_model_id or None,
                year_from=year_from_int,
                year_to=year_to_int,
                title=title.strip(),
                description=description.strip() if description else "",
                severity=severity
            )
            CommonErrorRepository.create(error)
            return {"success": True, "message": "Error común registrado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al guardar: {e}"}

    @staticmethod
    def update(error_id: str, brand_id: str, vehicle_model_id: str, year_from, year_to,
               title: str, description: str, severity: str) -> Dict:
        if not title or not title.strip():
            return {"success": False, "message": "El título es obligatorio"}
        if severity not in CommonErrorModel.SEVERITIES:
            severity = "media"
        try:
            year_from_int = int(year_from) if year_from else None
            year_to_int = int(year_to) if year_to else None
        except (ValueError, TypeError):
            return {"success": False, "message": "El año debe ser un número válido"}
        try:
            CommonErrorRepository.update_by_id(error_id, {
                "brand_id": brand_id or None,
                "vehicle_model_id": vehicle_model_id or None,
                "year_from": year_from_int,
                "year_to": year_to_int,
                "title": title.strip(),
                "description": description.strip() if description else "",
                "severity": severity
            })
            return {"success": True, "message": "Error común actualizado exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al actualizar: {e}"}

    @staticmethod
    def delete(error_id: str) -> Dict:
        try:
            CommonErrorRepository.delete_by_id(error_id)
            return {"success": True, "message": "Registro eliminado"}
        except Exception as e:
            return {"success": False, "message": f"Error al eliminar: {e}"}
