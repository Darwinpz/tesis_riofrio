from datetime import datetime

class WorkOrderModel:
    VALID_STATUSES = ["ingresado", "revision", "resultado", "finalizado"]
    STATUS_LABELS = {
        "ingresado": "Ingresado",
        "revision": "En Revisión",
        "resultado": "Resultado del Chequeo",
        "finalizado": "Finalizado",
        # backward compat with old records
        "abierta": "Ingresado",
        "en_proceso": "En Revisión",
        "cerrada": "Finalizado",
    }

    def __init__(self, number, client_id, vehicle_brand, vehicle_model, vehicle_plate,
                 parts=None, labor_cost=0.0, total=0.0, status="ingresado",
                 operator_id=None, mechanic_id=None, notes=None, vehicle_photos=None, id=None):
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
        self.mechanic_id = mechanic_id
        self.notes = notes
        self.vehicle_photos = vehicle_photos or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def is_closed(self):
        return self.status in ("finalizado", "cerrada")

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
            status=data.get("status", "ingresado"),
            operator_id=data.get("operator_id"),
            mechanic_id=data.get("mechanic_id"),
            notes=data.get("notes"),
            vehicle_photos=data.get("vehicle_photos", [])
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
            "mechanic_id": self.mechanic_id,
            "notes": self.notes,
            "vehicle_photos": self.vehicle_photos,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def __repr__(self):
        return f"WorkOrderModel(number={self.number}, status={self.status}, total={self.total})"
