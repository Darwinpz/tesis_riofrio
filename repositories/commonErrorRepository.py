from bson import ObjectId
from database.mongoDb import DatabaseConnection
from pymongo.errors import PyMongoError


class CommonErrorRepository:
    COLLECTION_NAME = "common_errors"

    @classmethod
    def _col(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def find_all(cls, brand_id: str = None, vehicle_model_id: str = None) -> list:
        from models.commonErrorModel import CommonErrorModel
        try:
            query = {}
            if brand_id:
                query["brand_id"] = brand_id
            if vehicle_model_id:
                query["vehicle_model_id"] = vehicle_model_id
            docs = cls._col().find(query).sort("created_at", -1)
            return [CommonErrorModel.from_dict(d) for d in docs]
        except PyMongoError as e:
            print(f"Error al obtener errores comunes: {e}")
            raise

    @classmethod
    def find_by_id(cls, error_id: str):
        from models.commonErrorModel import CommonErrorModel
        try:
            doc = cls._col().find_one({"_id": ObjectId(error_id)})
            return CommonErrorModel.from_dict(doc) if doc else None
        except PyMongoError as e:
            print(f"Error al buscar error común: {e}")
            raise

    @classmethod
    def create(cls, error) -> None:
        try:
            result = cls._col().insert_one(error.to_dict())
            error.id = str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear error común: {e}")
            raise

    @classmethod
    def update_by_id(cls, error_id: str, data: dict) -> None:
        try:
            cls._col().update_one({"_id": ObjectId(error_id)}, {"$set": data})
        except PyMongoError as e:
            print(f"Error al actualizar error común: {e}")
            raise

    @classmethod
    def delete_by_id(cls, error_id: str) -> None:
        try:
            cls._col().delete_one({"_id": ObjectId(error_id)})
        except PyMongoError as e:
            print(f"Error al eliminar error común: {e}")
            raise
