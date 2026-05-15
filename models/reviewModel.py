from datetime import datetime

class ReviewModel:
    SUBJECT_TYPES = ["part", "service"]

    def __init__(self, subject_type, subject_id, user_id, user_name, rating, comment=None, id=None):
        self.id = id
        self.subject_type = subject_type  # "part" | "service"
        self.subject_id = subject_id
        self.user_id = user_id
        self.user_name = user_name
        self.rating = rating  # 1-5
        self.comment = comment
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'ReviewModel':
        r = cls(
            subject_type=data["subject_type"],
            subject_id=data["subject_id"],
            user_id=data["user_id"],
            user_name=data.get("user_name", ""),
            rating=data["rating"],
            comment=data.get("comment")
        )
        if "_id" in data:
            r.id = str(data["_id"])
        if "created_at" in data:
            r.created_at = data["created_at"]
        return r

    def to_dict(self) -> dict:
        return {
            "subject_type": self.subject_type,
            "subject_id": self.subject_id,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at
        }
