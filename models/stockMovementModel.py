from datetime import datetime

class StockMovementModel:
    ENTRY_MOTIVES = ["compra", "devolucion", "ajuste"]
    EXIT_MOTIVES = ["orden_trabajo", "venta_directa", "ajuste", "danio"]

    def __init__(self, spare_part_id, movement_type, quantity, motive,
                 note=None, user_id=None, work_order_id=None, id=None):
        self.id = id
        self.spare_part_id = spare_part_id
        self.movement_type = movement_type  # "entrada" | "salida"
        self.quantity = quantity
        self.motive = motive
        self.note = note
        self.user_id = user_id
        self.work_order_id = work_order_id
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'StockMovementModel':
        mv = cls(
            spare_part_id=data["spare_part_id"],
            movement_type=data["movement_type"],
            quantity=data["quantity"],
            motive=data["motive"],
            note=data.get("note"),
            user_id=data.get("user_id"),
            work_order_id=data.get("work_order_id")
        )
        if "_id" in data:
            mv.id = str(data["_id"])
        if "created_at" in data:
            mv.created_at = data["created_at"]
        return mv

    def to_dict(self) -> dict:
        return {
            "spare_part_id": self.spare_part_id,
            "movement_type": self.movement_type,
            "quantity": self.quantity,
            "motive": self.motive,
            "note": self.note,
            "user_id": self.user_id,
            "work_order_id": self.work_order_id,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"StockMovementModel(type={self.movement_type}, qty={self.quantity}, part={self.spare_part_id})"
