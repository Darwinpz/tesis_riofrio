from database.mongoDb import DatabaseConnection
from models.workOrderModel import WorkOrderModel
from typing import List, Optional, Tuple
from bson import ObjectId
from pymongo.errors import PyMongoError

class WorkOrderRepository:
    COLLECTION_NAME = "work_orders"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, order: WorkOrderModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(order.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear orden de trabajo en la BD: {e}")
            raise

    @classmethod
    def find_paginated(cls, page: int, per_page: int, search: str = None,
                       status: str = None, client_id: str = None) -> Tuple[List[WorkOrderModel], int]:
        try:
            collection = cls._get_collection()
            query = {}
            if search:
                query["$or"] = [
                    {"number": {"$regex": search, "$options": "i"}},
                    {"vehicle_plate": {"$regex": search, "$options": "i"}}
                ]
            if status:
                query["status"] = status
            if client_id:
                query["client_id"] = client_id
            total = collection.count_documents(query)
            skip = (page - 1) * per_page
            orders = [WorkOrderModel.from_dict(o) for o in
                      collection.find(query).sort("created_at", -1).skip(skip).limit(per_page)]
            return orders, total
        except PyMongoError as e:
            print(f"Error al obtener órdenes paginadas en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, order_id: str) -> Optional[WorkOrderModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(order_id)})
            if data:
                return WorkOrderModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar orden por ID en la BD: {e}")
            raise

    @classmethod
    def find_by_client(cls, client_id: str) -> List[WorkOrderModel]:
        try:
            collection = cls._get_collection()
            return [WorkOrderModel.from_dict(o) for o in
                    collection.find({"client_id": client_id}).sort("created_at", -1)]
        except PyMongoError as e:
            print(f"Error al buscar órdenes del cliente en la BD: {e}")
            raise

    @classmethod
    def update_by_id(cls, order_id: str, update_data: dict) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(order_id)}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar orden en la BD: {e}")
            raise

    @classmethod
    def find_by_mechanic(cls, mechanic_id: str) -> List[WorkOrderModel]:
        try:
            collection = cls._get_collection()
            return [WorkOrderModel.from_dict(o) for o in
                    collection.find({"mechanic_id": mechanic_id}).sort("created_at", -1)]
        except PyMongoError as e:
            print(f"Error al buscar órdenes del mecánico en la BD: {e}")
            raise

    @classmethod
    def count_active(cls) -> int:
        try:
            active = ["ingresado", "revision", "resultado", "abierta", "en_proceso"]
            return cls._get_collection().count_documents({"status": {"$in": active}})
        except PyMongoError as e:
            print(f"Error al contar órdenes activas en la BD: {e}")
            raise

    @classmethod
    def get_next_number(cls) -> str:
        try:
            collection = cls._get_collection()
            last = collection.find_one({}, sort=[("created_at", -1)])
            if last and "number" in last:
                try:
                    num = int(last["number"].split("-")[1]) + 1
                except Exception:
                    num = 1
            else:
                num = 1
            return f"OT-{num:04d}"
        except PyMongoError as e:
            print(f"Error al obtener siguiente número de OT en la BD: {e}")
            raise
