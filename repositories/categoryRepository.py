from database.mongoDb import DatabaseConnection
from models.categoryModel import CategoryModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class CategoryRepository:
    COLLECTION_NAME = "categories"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, category: CategoryModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(category.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear categoría en la BD: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[CategoryModel]:
        try:
            collection = cls._get_collection()
            return [CategoryModel.from_dict(c) for c in collection.find().sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener categorías en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, category_id: str) -> Optional[CategoryModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(category_id)})
            if data:
                return CategoryModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar categoría por ID en la BD: {e}")
            raise

    @classmethod
    def exist_by_name(cls, name: str, exclude_id: str = None) -> bool:
        try:
            collection = cls._get_collection()
            query = {"name": name}
            if exclude_id:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            return collection.find_one(query) is not None
        except PyMongoError as e:
            print(f"Error al verificar nombre de categoría en la BD: {e}")
            raise

    @classmethod
    def update_by_id(cls, category_id: str, update_data: dict) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(category_id)}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar categoría en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, category_id: str) -> None:
        try:
            collection = cls._get_collection()
            collection.delete_one({"_id": ObjectId(category_id)})
        except PyMongoError as e:
            print(f"Error al eliminar categoría en la BD: {e}")
            raise
