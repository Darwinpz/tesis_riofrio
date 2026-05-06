from datetime import datetime

class VehicleModelModel:
    def __init__(self, name, description=None, brand_id=None, id=None):
        self.id = id
        self.name = name
        self.description = description
        self.brand_id = brand_id   # referencia opcional a la marca
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'VehicleModelModel':
        vm = cls(
            name=data["name"],
            description=data.get("description"),
            brand_id=data.get("brand_id")
        )
        if "_id" in data:
            vm.id = str(data["_id"])
        if "created_at" in data:
            vm.created_at = data["created_at"]
        return vm

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "brand_id": self.brand_id,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"VehicleModelModel(name={self.name})"
