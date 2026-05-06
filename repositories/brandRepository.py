from database.mongoDb import DatabaseConnection
from models.brandModel import BrandModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class BrandRepository:
    COLLECTION_NAME = "brands"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, brand: BrandModel) -> str:
        try:
            result = cls._get_collection().insert_one(brand.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear marca en la BD: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[BrandModel]:
        try:
            return [BrandModel.from_dict(b) for b in cls._get_collection().find().sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener marcas en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, brand_id: str) -> Optional[BrandModel]:
        try:
            data = cls._get_collection().find_one({"_id": ObjectId(brand_id)})
            return BrandModel.from_dict(data) if data else None
        except PyMongoError as e:
            print(f"Error al buscar marca por ID en la BD: {e}")
            raise

    @classmethod
    def exist_by_name(cls, name: str, exclude_id: str = None) -> bool:
        try:
            query = {"name": name}
            if exclude_id:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            return cls._get_collection().find_one(query) is not None
        except PyMongoError as e:
            print(f"Error al verificar nombre de marca en la BD: {e}")
            raise

    @classmethod
    def update_by_id(cls, brand_id: str, update_data: dict) -> None:
        try:
            cls._get_collection().update_one({"_id": ObjectId(brand_id)}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar marca en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, brand_id: str) -> None:
        try:
            cls._get_collection().delete_one({"_id": ObjectId(brand_id)})
        except PyMongoError as e:
            print(f"Error al eliminar marca en la BD: {e}")
            raise
