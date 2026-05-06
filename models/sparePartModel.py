from datetime import datetime

class SparePartModel:
    def __init__(self, code, name, description=None, brand_id=None, vehicle_model_id=None,
                 category_id=None, supplier_id=None,
                 stock_actual=0, stock_minimo=0, stock_maximo=0, precio_compra=0.0,
                 precio_venta=0.0, ubicacion=None, imagen=None, is_active=True, id=None):
        self.id = id
        self.code = code
        self.name = name
        self.description = description
        self.brand_id = brand_id
        self.vehicle_model_id = vehicle_model_id
        self.category_id = category_id
        self.supplier_id = supplier_id
        self.stock_actual = stock_actual
        self.stock_minimo = stock_minimo
        self.stock_maximo = stock_maximo
        self.precio_compra = precio_compra
        self.precio_venta = precio_venta
        self.ubicacion = ubicacion
        self.imagen = imagen
        self.is_active = is_active
        self.created_at = datetime.now()

    @classmethod
    def from_dict(cls, data: dict) -> 'SparePartModel':
        part = cls(
            code=data["code"],
            name=data["name"],
            description=data.get("description"),
            brand_id=data.get("brand_id") or data.get("marca"),
            vehicle_model_id=data.get("vehicle_model_id") or data.get("modelo"),
            category_id=data.get("category_id"),
            supplier_id=data.get("supplier_id"),
            stock_actual=data.get("stock_actual", 0),
            stock_minimo=data.get("stock_minimo", 0),
            stock_maximo=data.get("stock_maximo", 0),
            precio_compra=data.get("precio_compra", 0.0),
            precio_venta=data.get("precio_venta", 0.0),
            ubicacion=data.get("ubicacion"),
            imagen=data.get("imagen"),
            is_active=data.get("is_active", True)
        )
        if "_id" in data:
            part.id = str(data["_id"])
        if "created_at" in data:
            part.created_at = data["created_at"]
        return part

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "brand_id": self.brand_id,
            "vehicle_model_id": self.vehicle_model_id,
            "category_id": self.category_id,
            "supplier_id": self.supplier_id,
            "stock_actual": self.stock_actual,
            "stock_minimo": self.stock_minimo,
            "stock_maximo": self.stock_maximo,
            "precio_compra": self.precio_compra,
            "precio_venta": self.precio_venta,
            "ubicacion": self.ubicacion,
            "imagen": self.imagen,
            "is_active": self.is_active,
            "created_at": self.created_at
        }

    def __repr__(self):
        return f"SparePartModel(code={self.code}, name={self.name}, stock={self.stock_actual})"
