from datetime import datetime

_LEGACY_MAP = {
    "ingresado": "recepcion", "abierta": "recepcion",
    "revision": "diagnostico", "en_proceso": "diagnostico",
    "resultado": "presupuesto",
    "finalizado": "entregado", "cerrada": "entregado",
}

class WorkOrderModel:
    STATUS_FLOW = [
        "recepcion", "diagnostico", "presupuesto",
        "aprobado", "en_reparacion", "pago_pendiente", "entregado"
    ]
    VALID_STATUSES = STATUS_FLOW

    STATUS_LABELS = {
        "recepcion":      "Recepción",
        "diagnostico":    "En Diagnóstico",
        "presupuesto":    "Presupuesto Emitido",
        "aprobado":       "Aprobado",
        "en_reparacion":  "En Reparación",
        "pago_pendiente": "Pago Pendiente",
        "entregado":      "Entregado",
        # backward compat
        "ingresado": "Recepción",  "revision":  "En Diagnóstico",
        "resultado": "Presupuesto Emitido", "finalizado": "Entregado",
        "abierta":   "Recepción",  "en_proceso": "En Diagnóstico",
        "cerrada":   "Entregado",
    }

    # Roles allowed to advance FROM each status
    STATUS_TRANSITIONS = {
        "recepcion":      ["admin", "operator"],
        "diagnostico":    ["admin", "operator", "mechanic"],
        "presupuesto":    ["admin", "operator", "client"],
        "aprobado":       ["admin", "operator", "mechanic"],
        "en_reparacion":  ["admin", "operator", "mechanic"],
        "pago_pendiente": ["admin", "operator"],
    }

    # (button label, description)
    STATUS_ADVANCE_LABELS = {
        "recepcion":      ("Enviar a Diagnóstico",
                           "El vehículo está registrado. Asigna mecánico si corresponde y envía a diagnóstico."),
        "diagnostico":    ("Emitir Presupuesto",
                           "El mecánico completó el diagnóstico. Genera el presupuesto para aprobación del cliente."),
        "presupuesto":    ("Marcar como Aprobado",
                           "El cliente aceptó el presupuesto. Autoriza el inicio de la reparación."),
        "aprobado":       ("Iniciar Reparación",
                           "Presupuesto aprobado. El mecánico puede comenzar el trabajo."),
        "en_reparacion":  ("Trabajo Terminado",
                           "La reparación está completa. El vehículo está listo para entrega y pago."),
        "pago_pendiente": ("Confirmar Entrega y Cobro",
                           "Se descontará el stock de repuestos y el ingreso quedará cerrado. Esta acción no se puede deshacer."),
    }

    def __init__(self, number, client_id, vehicle_brand, vehicle_model, vehicle_plate,
                 vehicle_year=None, parts=None, labor_cost=0.0, total=0.0, status="recepcion",
                 operator_id=None, mechanic_id=None, notes=None, vehicle_photos=None,
                 status_history=None, payment_proof_path=None,
                 work_notes=None, work_photos=None, id=None):
        self.id = id
        self.number = number
        self.client_id = client_id
        self.vehicle_brand = vehicle_brand
        self.vehicle_model = vehicle_model
        self.vehicle_plate = vehicle_plate
        self.vehicle_year = vehicle_year
        self.parts = parts or []
        self.labor_cost = labor_cost
        self.total = total
        self.status = status
        self.operator_id = operator_id
        self.mechanic_id = mechanic_id
        self.notes = notes
        self.vehicle_photos = vehicle_photos or []
        self.status_history = status_history or []
        self.payment_proof_path = payment_proof_path
        self.work_notes = work_notes
        self.work_photos = work_photos or []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    @property
    def canonical_status(self):
        return _LEGACY_MAP.get(self.status, self.status)

    @property
    def status_label(self):
        return self.STATUS_LABELS.get(self.status, self.status)

    @property
    def status_index(self):
        s = self.canonical_status
        try:
            return self.STATUS_FLOW.index(s)
        except ValueError:
            return 0

    @property
    def next_status(self):
        idx = self.status_index
        if idx < len(self.STATUS_FLOW) - 1:
            return self.STATUS_FLOW[idx + 1]
        return None

    @property
    def prev_status(self):
        idx = self.status_index
        if idx > 0:
            return self.STATUS_FLOW[idx - 1]
        return None

    @property
    def is_closed(self):
        return self.canonical_status == "entregado"

    def can_user_advance(self, user_role: str) -> bool:
        canonical = self.canonical_status
        allowed = self.STATUS_TRANSITIONS.get(canonical, [])
        return user_role in allowed

    def can_user_revert(self, user_role: str) -> bool:
        if user_role not in ("admin", "operator"):
            return False
        canonical = self.canonical_status
        return canonical not in ("recepcion", "entregado")

    @classmethod
    def from_dict(cls, data: dict) -> 'WorkOrderModel':
        order = cls(
            number=data["number"],
            client_id=data["client_id"],
            vehicle_brand=data["vehicle_brand"],
            vehicle_model=data["vehicle_model"],
            vehicle_plate=data["vehicle_plate"],
            vehicle_year=data.get("vehicle_year"),
            parts=data.get("parts", []),
            labor_cost=data.get("labor_cost", 0.0),
            total=data.get("total", 0.0),
            status=data.get("status", "recepcion"),
            operator_id=data.get("operator_id"),
            mechanic_id=data.get("mechanic_id"),
            notes=data.get("notes"),
            vehicle_photos=data.get("vehicle_photos", []),
            status_history=data.get("status_history", []),
            payment_proof_path=data.get("payment_proof_path"),
            work_notes=data.get("work_notes"),
            work_photos=data.get("work_photos", []),
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
            "vehicle_year": self.vehicle_year,
            "parts": self.parts,
            "labor_cost": self.labor_cost,
            "total": self.total,
            "status": self.status,
            "operator_id": self.operator_id,
            "mechanic_id": self.mechanic_id,
            "notes": self.notes,
            "vehicle_photos": self.vehicle_photos,
            "status_history": self.status_history,
            "payment_proof_path": self.payment_proof_path,
            "work_notes": self.work_notes,
            "work_photos": self.work_photos,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def __repr__(self):
        return f"WorkOrderModel(number={self.number}, status={self.status}, total={self.total})"
