from datetime import datetime

class WorkOrderModel:
    VALID_STATUSES = ["abierta", "en_proceso", "cerrada"]

    def __init__(self, number, client_id, vehicle_brand, vehicle_model, vehicle_plate,
                 parts=None, labor_cost=0.0, total=0.0, status="abierta",
                 operator_id=None, notes=None, id=None):
        self.id = id
        self.number = number
        self.client_id = client_id
        self.vehicle_brand = vehicle_brand
        self.vehicle_model = vehicle_model
        self.vehicle_plate = vehicle_plate
        self.parts = parts or []
        self.labor_cost = labor_cost
        self.total = total
        self.status = status
        self.operator_id = operator_id
        self.notes = notes
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkOrderModel':
        order = cls(
            number=data["number"],
            client_id=data["client_id"],
            vehicle_brand=data["vehicle_brand"],
            vehicle_model=data["vehicle_model"],
            vehicle_plate=data["vehicle_plate"],
            parts=data.get("parts", []),
            labor_cost=data.get("labor_cost", 0.0),
            total=data.get("total", 0.0),
            status=data.get("status", "abierta"),
            operator_id=data.get("operator_id"),
            notes=data.get("notes")
        )
        if "_id" in data:
            order.id = str(data["_id"])
        if "created_at" in data:
            order.created_at = data["created_at"]
        if "updated_at" in data:
            order.updated_at = data["updated_at"]
        return order

    def to_dict(self) -> dict:
        return {
            "number": self.number,
            "client_id": self.client_id,
            "vehicle_brand": self.vehicle_brand,
            "vehicle_model": self.vehicle_model,
            "vehicle_plate": self.vehicle_plate,
            "parts": self.parts,
            "labor_cost": self.labor_cost,
            "total": self.total,
            "status": self.status,
            "operator_id": self.operator_id,
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def __repr__(self):
        return f"WorkOrderModel(number={self.number}, status={self.status}, total={self.total})"
