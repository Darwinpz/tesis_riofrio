from typing import Dict
from repositories.reviewRepository import ReviewRepository


class ReviewService:

    @staticmethod
    def get_for_subject(subject_type: str, subject_id: str) -> Dict:
        try:
            reviews = ReviewRepository.find_by_subject(subject_type, subject_id)
            stats = ReviewRepository.get_avg_rating(subject_type, subject_id)
            return {"success": True, "reviews": reviews, "stats": stats}
        except Exception as e:
            return {"success": False, "message": str(e), "reviews": [], "stats": {"avg": 0.0, "count": 0}}

    @staticmethod
    def submit(subject_type: str, subject_id: str, user_id: str, user_name: str,
               rating: int, comment: str) -> Dict:
        try:
            rating = int(rating)
        except (ValueError, TypeError):
            return {"success": False, "message": "Calificación inválida"}
        if not 1 <= rating <= 5:
            return {"success": False, "message": "La calificación debe ser entre 1 y 5"}
        try:
            ReviewRepository.upsert_by_user_and_subject(
                user_id, subject_type, subject_id, rating, comment or "", user_name
            )
            return {"success": True, "message": "Reseña publicada exitosamente"}
        except Exception as e:
            return {"success": False, "message": f"Error al guardar reseña: {e}"}

    @staticmethod
    def get_user_review(user_id: str, subject_type: str, subject_id: str):
        try:
            return ReviewRepository.find_by_user_and_subject(user_id, subject_type, subject_id)
        except Exception:
            return None
