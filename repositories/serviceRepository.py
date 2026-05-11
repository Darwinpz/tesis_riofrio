from database.mongoDb import DatabaseConnection
from models.serviceModel import ServiceModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class ServiceRepository:
    COLLECTION_NAME = "services"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, service: ServiceModel) -> str:
        try:
            result = cls._get_collection().insert_one(service.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear servicio en la BD: {e}")
            raise

    @classmethod
    def find_all_active(cls) -> List[ServiceModel]:
        try:
            return [ServiceModel.from_dict(s) for s in
                    cls._get_collection().find({"is_active": True}).sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener servicios en la BD: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[ServiceModel]:
        try:
            return [ServiceModel.from_dict(s) for s in
                    cls._get_collection().find().sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener servicios en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, service_id: str) -> Optional[ServiceModel]:
        try:
            data = cls._get_collection().find_one({"_id": ObjectId(service_id)})
            return ServiceModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar servicio por ID en la BD: {e}")
            raise

    @classmethod
    def exist_by_name(cls, name: str, exclude_id: str = None) -> bool:
        try:
            query = {"name": name}
            if exclude_id:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            return cls._get_collection().find_one(query) is not None
        except PyMongoError as e:
            print(f"Error al verificar nombre de servicio en la BD: {e}")
            raise

    @classmethod
    def update_by_id(cls, service_id: str, update_data: dict) -> None:
        try:
            cls._get_collection().update_one({"_id": ObjectId(service_id)}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar servicio en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, service_id: str) -> None:
        try:
            cls._get_collection().delete_one({"_id": ObjectId(service_id)})
        except PyMongoError as e:
            print(f"Error al eliminar servicio en la BD: {e}")
            raise
