from database.mongoDb import DatabaseConnection
from models.personModel import PersonModel
from typing import Optional
from pymongo.errors import PyMongoError

class PersonRepository:
    # Repositorio para operaciones con la BD de persistencia de datos personales del usuario

    COLLECTION_NAME = "persons"

    @classmethod
    def _get_collection(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)
    
    @classmethod
    def create(cls, person: PersonModel) -> str:
        #Crea una nueva persona en la bd
        try:
            collection = cls._get_collection()
            result = collection.insert_one(person.to_dict())
            return str(result.inserted_id)
        except PyMongoError as e:
            print(f"Error al crear una nueva persona en la BD: {e}")
            raise
    
    @classmethod
    def find_by_user_id(cls, user_id: str) -> Optional[PersonModel]:
        #Buscar datos por user_id de la colección user
        try:
            collection = cls._get_collection()
            data = collection.find_one({"user_id": user_id})
            if data:
                return PersonModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar la persona por Id en la BD: {e}")
            raise
    
    @classmethod
    def find_by_identification(cls, identification: str) -> Optional[PersonModel]:
        #Buscar datos por identificacion
        try:
            collection = cls._get_collection()
            data = collection.find_one({"identification": identification})
            if data:
                return PersonModel.from_dict(data)
            return None
        except PyMongoError as e:
            print(f"Error al buscar la persona por identificacion en la BD: {e}")
            raise
    
    @classmethod
    def exist_by_identification(cls, identification: str) -> bool:
        #Existe identificacion
        try:
            collection = cls._get_collection()
            return collection.find_one({"identification": identification}) is not None
        except PyMongoError as e:
            print(f"Error al buscar una identificacion en la BD: {e}")
            raise

    @classmethod
    def update_by_user_id(cls, user_id: str, update_data: dict) -> None:
        #Actualizar datos personales por user_id
        try:
            collection = cls._get_collection()
            collection.update_one({"user_id": user_id}, {"$set": update_data})
        except PyMongoError as e:
            print(f"Error al actualizar la persona por user_id en la BD: {e}")
            raise

    @classmethod
    def delete_by_user_id(cls, user_id: str) -> None:
        #Eliminar persona por user_id
        try:
            collection = cls._get_collection()
            collection.delete_one({"user_id": user_id})
        except PyMongoError as e:
            print(f"Error al eliminar la persona por user_id en la BD: {e}")
            raise