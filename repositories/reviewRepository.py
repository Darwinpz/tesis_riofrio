from bson import ObjectId
from database.mongoDb import DatabaseConnection
from pymongo.errors import PyMongoError


class ReviewRepository:
    COLLECTION_NAME = "reviews"

    @classmethod
    def _col(cls):
        return DatabaseConnection.get_collection(cls.COLLECTION_NAME)

    @classmethod
    def find_by_subject(cls, subject_type: str, subject_id: str) -> list:
        from models.reviewModel import ReviewModel
        try:
            docs = cls._col().find(
                {"subject_type": subject_type, "subject_id": subject_id}
            ).sort("created_at", -1)
            return [ReviewModel.from_dict(d) for d in docs]
        except PyMongoError as e:
            print(f"Error al obtener reseñas: {e}")
            raise

    @classmethod
    def find_by_user_and_subject(cls, user_id: str, subject_type: str, subject_id: str):
        from models.reviewModel import ReviewModel
        try:
            doc = cls._col().find_one({
                "user_id": user_id,
                "subject_type": subject_type,
                "subject_id": subject_id
            })
            return ReviewModel.from_dict(doc) if doc else None
        except PyMongoError as e:
            print(f"Error al buscar reseña: {e}")
            raise

    @classmethod
    def upsert_by_user_and_subject(cls, user_id: str, subject_type: str, subject_id: str,
                                   rating: int, comment: str, user_name: str) -> None:
        from datetime import datetime
        try:
            cls._col().update_one(
                {"user_id": user_id, "subject_type": subject_type, "subject_id": subject_id},
                {"$set": {"rating": rating, "comment": comment, "user_name": user_name,
                          "created_at": datetime.now()}},
                upsert=True
            )
        except PyMongoError as e:
            print(f"Error al guardar reseña: {e}")
            raise

    @classmethod
    def get_avg_rating(cls, subject_type: str, subject_id: str) -> dict:
        try:
            pipeline = [
                {"$match": {"subject_type": subject_type, "subject_id": subject_id}},
                {"$group": {"_id": None, "avg": {"$avg": "$rating"}, "count": {"$sum": 1}}}
            ]
            result = list(cls._col().aggregate(pipeline))
            if result:
                return {"avg": round(result[0]["avg"], 1), "count": result[0]["count"]}
            return {"avg": 0.0, "count": 0}
        except PyMongoError as e:
            print(f"Error al calcular promedio: {e}")
            return {"avg": 0.0, "count": 0}
