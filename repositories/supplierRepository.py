from database.mongoDb import DatabaseConnection
from models.supplierModel import SupplierModel
from typing import List, Optional
from bson import ObjectId
from pymongo.errors import PyMongoError

class SupplierRepository:
    COLLECTION_NAME = "suppliers"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def create(cls, supplier: SupplierModel) -> str:
        try:
            collection = cls._get_collection()
            result = collection.insert_one(supplier.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear proveedor en la BD: {e}")
            raise

    @classmethod
    def find_all(cls) -> List[SupplierModel]:
        try:
            collection = cls._get_collection()
            return [SupplierModel.from_dict(s) for s in collection.find().sort("name", 1)]
        except PyMongoError as e:
            print(f"Error al obtener proveedores en la BD: {e}")
            raise

    @classmethod
    def find_by_id(cls, supplier_id: str) -> Optional[SupplierModel]:
        try:
            collection = cls._get_collection()
            data = collection.find_one({"_id": ObjectId(supplier_id)})
            if data:
                return SupplierModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar proveedor por ID en la BD: {e}")
            raise

    @classmethod
    def update_by_id(cls, supplier_id: str, update_data: dict) -> None:
        try:
            collection = cls._get_collection()
            collection.update_one({"_id": ObjectId(supplier_id)}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar proveedor en la BD: {e}")
            raise

    @classmethod
    def delete_by_id(cls, supplier_id: str) -> None:
        try:
            collection = cls._get_collection()
            collection.delete_one({"_id": ObjectId(supplier_id)})
        except PyMongoError as e:
            print(f"Error al eliminar proveedor en la BD: {e}")
            raise
