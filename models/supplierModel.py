from datetime import datetime

class SupplierModel:
    def __init__(self, name, contact=None, phone=None, email=None, address=None, id=None):
        self.id = id
        self.name = name
        self.contact = contact
        self.phone = phone
        self.email = email
        self.address = address
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'SupplierModel':
        supplier = cls(
            name=data["name"],
            contact=data.get("contact"),
            phone=data.get("phone"),
            email=data.get("email"),
            address=data.get("address")
        )
        if "_id" in data:
            supplier.id = str(data["_id"])
        if "created_at" in data:
            supplier.created_at = data["created_at"]
        return supplier

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "contact": self.contact,
            "phone": self.phone,
            "email": self.email,
            "address": self.address,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"SupplierModel(name={self.name})"
