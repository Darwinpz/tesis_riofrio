from datetime import datetime

class BrandModel:
    def __init__(self, name, description=None, id=None):
        self.id = id
        self.name = name
        self.description = description
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'BrandModel':
        brand = cls(
            name=data["name"],
            description=data.get("description")
        )
        if "_id" in data:
            brand.id = str(data["_id"])
        if "created_at" in data:
            brand.created_at = data["created_at"]
        return brand

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"BrandModel(name={self.name})"
