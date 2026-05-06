from database.mongoDb import DatabaseConnection
from models.stockMovementModel import StockMovementModel
from typing import List
from bson import ObjectId
from pymongo.errors import PyMongoError
from datetime import datetime, timedelta

class StockMovementRepository:
    COLLECTION_NAME = "stock_movements"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, movement: StockMovementModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(movement.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear movimiento en la BD: {e}")
            raise

    @classmethod
    def find_paginated(cls, page: int, per_page: int, spare_part_id: str = None,
                       movement_type: str = None, start_date: datetime = None,
                       end_date: datetime = None) -> tuple:
        try:
            collection = cls._get_collection()
            query = {}
            if spare_part_id:
                query["spare_part_id"] = spare_part_id
            if movement_type:
                query["movement_type"] = movement_type
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["created_at"] = date_filter
            total = collection.count_documents(query)
            skip = (page - 1) * per_page
            movements = [StockMovementModel.from_dict(m) for m in
                         collection.find(query).sort("created_at", -1).skip(skip).limit(per_page)]
            return movements, total
        except PyMongoError as e:
            print(f"Error al obtener movimientos paginados en la BD: {e}")
            raise

    @classmethod
    def find_by_spare_part(cls, spare_part_id: str) -> List[StockMovementModel]:
        try:
            collection = cls._get_collection()
            return [StockMovementModel.from_dict(m) for m in
                    collection.find({"spare_part_id": spare_part_id}).sort("created_at", -1).limit(50)]
        except PyMongoError as e:
            print(f"Error al obtener movimientos del repuesto en la BD: {e}")
            raise

    @classmethod
    def has_movements_for_part(cls, spare_part_id: str) -> bool:
        try:
            return cls._get_collection().find_one({"spare_part_id": spare_part_id}) is not None
        except PyMongoError as e:
            print(f"Error al verificar movimientos del repuesto en la BD: {e}")
            raise

    @classmethod
    def count_today(cls) -> int:
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            return cls._get_collection().count_documents({"created_at": {"$gte": today}})
        except PyMongoError as e:
            print(f"Error al contar movimientos de hoy en la BD: {e}")
            raise

    @classmethod
    def count_by_day(cls, days: int = 7) -> List[dict]:
        #Retorna conteo de movimientos por día para los últimos N días
        try:
            collection = cls._get_collection()
            start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=days - 1)
            pipeline = [
                {"$match": {"created_at": {"$gte": start}}},
                {"$group": {
                    "_id": {
                        "year": {"$year": "$created_at"},
                        "month": {"$month": "$created_at"},
                        "day": {"$dayOfMonth": "$created_at"},
                        "type": "$movement_type"
                    },
                    "count": {"$sum": 1}
                }},
                {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1}}
            ]
            return list(collection.aggregate(pipeline))
        except PyMongoError as e:
            print(f"Error al obtener movimientos por día en la BD: {e}")
            raise

    @classmethod
    def find_all_filtered(cls, spare_part_id: str = None, movement_type: str = None,
                          start_date: datetime = None, end_date: datetime = None) -> List[StockMovementModel]:
        try:
            collection = cls._get_collection()
            query = {}
            if spare_part_id:
                query["spare_part_id"] = spare_part_id
            if movement_type:
                query["movement_type"] = movement_type
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = start_date
                if end_date:
                    date_filter["$lte"] = end_date
                query["created_at"] = date_filter
            return [StockMovementModel.from_dict(m) for m in collection.find(query).sort("created_at", -1)]
        except PyMongoError as e:
            print(f"Error al obtener movimientos filtrados en la BD: {e}")
            raise
