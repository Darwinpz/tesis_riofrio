from datetime import datetime

class ServiceModel:
    def __init__(self, name, description=None, price=0.0, is_active=True, id=None):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.is_active = is_active
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'ServiceModel':
        svc = cls(
            name=data["name"],
            description=data.get("description"),
            price=data.get("price", 0.0),
            is_active=data.get("is_active", True)
        )
        if "_id" in data:
            svc.id = str(data["_id"])
        if "created_at" in data:
            svc.created_at = data["created_at"]
        return svc

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"ServiceModel(name={self.name}, price={self.price})"
