from database.mongoDb import DatabaseConnection
from models.vehicleModelModel import VehicleModelModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class VehicleModelRepository:
    COLLECTION_NAME = "vehicle_models"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, vm: VehicleModelModel) -> str:
        try:
            result = cls._get_collection().insert_one(vm.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear modelo de vehículo en la BD: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[VehicleModelModel]:
        try:
            return [VehicleModelModel.from_dict(v) for v in cls._get_collection().find().sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener modelos de vehículo en la BD: {e}")
            raise

    @classmethod
    def find_by_brand(cls, brand_id: str) -> List[VehicleModelModel]:
        try:
            return [VehicleModelModel.from_dict(v) for v in
                    cls._get_collection().find({"brand_id": brand_id}).sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener modelos por marca en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, vm_id: str) -> Optional[VehicleModelModel]:
        try:
            data = cls._get_collection().find_one({"_id": ObjectId(vm_id)})
            return VehicleModelModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar modelo de vehículo por ID en la BD: {e}")
            raise

    @classmethod
    def exist_by_name(cls, name: str, brand_id: str = None, exclude_id: str = None) -> bool:
        try:
            query = {"name": name}
            if brand_id:
                query["brand_id"] = brand_id
            if exclude_id:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            return cls._get_collection().find_one(query) is not None
        except PyMongoError as e:
            print(f"Error al verificar nombre de modelo en la BD: {e}")
            raise

    @classmethod
    def update_by_id(cls, vm_id: str, update_data: dict) -> None:
        try:
            cls._get_collection().update_one({"_id": ObjectId(vm_id)}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar modelo de vehículo en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, vm_id: str) -> None:
        try:
            cls._get_collection().delete_one({"_id": ObjectId(vm_id)})
        except PyMongoError as e:
            print(f"Error al eliminar modelo de vehículo en la BD: {e}")
            raise
