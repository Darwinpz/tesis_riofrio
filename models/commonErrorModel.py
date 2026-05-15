from datetime import datetime


class CommonErrorModel:
    SEVERITIES = ["baja", "media", "alta"]

    def __init__(self, brand_id, vehicle_model_id, year_from, year_to,
                 title, description, severity="media", id=None):
        self.id = id
        self.brand_id = brand_id
        self.vehicle_model_id = vehicle_model_id
        self.year_from = year_from  # int
        self.year_to = year_to      # int, can be None (= present)
        self.title = title
        self.description = description
        self.severity = severity
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'CommonErrorModel':
        err = cls(
            brand_id=data.get("brand_id"),
            vehicle_model_id=data.get("vehicle_model_id"),
            year_from=data.get("year_from"),
            year_to=data.get("year_to"),
            title=data["title"],
            description=data.get("description", ""),
            severity=data.get("severity", "media")
        )
        if "_id" in data:
            err.id = str(data["_id"])
        if "created_at" in data:
            err.created_at = data["created_at"]
        return err

    def to_dict(self) -> dict:
        return {
            "brand_id": self.brand_id,
            "vehicle_model_id": self.vehicle_model_id,
            "year_from": self.year_from,
            "year_to": self.year_to,
            "title": self.title,
            "description": self.description,
            "severity": self.severity,
            "created_at": self.created_at
        }

    @property
    def year_range_label(self) -> str:
        if self.year_from and self.year_to:
            return f"{self.year_from} – {self.year_to}"
        if self.year_from:
            return f"{self.year_from} – presente"
        return "Todos los años"
