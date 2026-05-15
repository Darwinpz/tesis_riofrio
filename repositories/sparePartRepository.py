from database.mongoDb import DatabaseConnection
from models.sparePartModel import SparePartModel
from typing import List, Optional, Tuple
from bson import ObjectId
from pymongo.errors import PyMongoError

class SparePartRepository:
    COLLECTION_NAME = "spare_parts"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, part: SparePartModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(part.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear repuesto en la BD: {e}")
            raise

    @classmethod
    def find_all_active(cls) -> List[SparePartModel]:
        try:
            collection = cls._get_collection()
            return [SparePartModel.from_dict(p) for p in collection.find({"is_active": True}).sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener repuestos en la BD: {e}")
            raise

    @classmethod
    def find_paginated(cls, page: int, per_page: int, search: str = None,
                       category_id: str = None, brand_id: str = None,
                       vehicle_model_id: str = None,
                       critical_only: bool = False) -> Tuple[List[SparePartModel], int]:
        try:
            collection = cls._get_collection()
            query = {"is_active": True}
            if search:
                query["$or"] = [
                    {"code": {"$regex": search, "$options": "i"}},
                    {"name": {"$regex": search, "$options": "i"}}
                ]
            if category_id:
                query["category_id"] = category_id
            if brand_id:
                query["brand_id"] = brand_id
            if vehicle_model_id:
                query["vehicle_model_id"] = vehicle_model_id
            if critical_only:
                query["$expr"] = {"$lte": ["$stock_actual", "$stock_minimo"]}
            total = collection.count_documents(query)
            skip = (page - 1) * per_page
            parts = [SparePartModel.from_dict(p) for p in
                     collection.find(query).sort("name", 1).skip(skip).limit(per_page)]
            return parts, total
        except PyMongoError as e:
            print(f"Error al obtener repuestos paginados en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, part_id: str) -> Optional[SparePartModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(part_id)})
            if data:
                return SparePartModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar repuesto por ID en la BD: {e}")
            raise

    @classmethod
    def get_next_code(cls) -> str:
        try:
            collection = cls._get_collection()
            docs = collection.find({"code": {"$regex": "^REP-\\d+$"}}, {"code": 1})
            max_num = 0
            for doc in docs:
                try:
                    num = int(doc["code"].split("-")[1])
                    if num > max_num:
                        max_num = num
                except Exception:
                    pass
            return f"REP-{max_num + 1:04d}"
        except PyMongoError as e:
            print(f"Error al generar código de repuesto en la BD: {e}")
            raise

    @classmethod
    def exist_by_code(cls, code: str, exclude_id: str = None) -> bool:
        try:
            collection = cls._get_collection()
            query = {"code": code}
            if exclude_id:
                query["_id"] = {"$ne": ObjectId(exclude_id)}
            return collection.find_one(query) is not None
        except PyMongoError as e:
            print(f"Error al verificar código de repuesto en la BD: {e}")
            raise

    @classmethod
    def update_by_id(cls, part_id: str, update_data: dict) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(part_id)}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar repuesto en la BD: {e}")
            raise

    @classmethod
    def update_stock(cls, part_id: str, new_stock: int) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(part_id)}, {"$set": {"stock_actual": new_stock}})
        except PyMongoError as e:
            print(f"Error al actualizar stock en la BD: {e}")
            raise

    @classmethod
    def find_critical_stock(cls) -> List[SparePartModel]:
        #Repuestos cuyo stock_actual <= stock_minimo
        try:
            collection = cls._get_collection()
            pipeline = [
                {"$match": {"is_active": True, "$expr": {"$lte": ["$stock_actual", "$stock_minimo"]}}},
                {"$sort": {"stock_actual": 1}}
            ]
            return [SparePartModel.from_dict(p) for p in collection.aggregate(pipeline)]
        except PyMongoError as e:
            print(f"Error al obtener repuestos críticos en la BD: {e}")
            raise

    @classmethod
    def count_active(cls) -> int:
        try:
            return cls._get_collection().count_documents({"is_active": True})
        except PyMongoError as e:
            print(f"Error al contar repuestos activos en la BD: {e}")
            raise

    @classmethod
    def count_critical(cls) -> int:
        try:
            pipeline = [{"$match": {"is_active": True, "$expr": {"$lte": ["$stock_actual", "$stock_minimo"]}}}]
            return len(list(cls._get_collection().aggregate(pipeline)))
        except PyMongoError as e:
            print(f"Error al contar repuestos críticos en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, part_id: str) -> None:
        try:
            collection = cls._get_collection()
            collection.delete_one({"_id": ObjectId(part_id)})
        except PyMongoError as e:
            print(f"Error al eliminar repuesto en la BD: {e}")
            raise
