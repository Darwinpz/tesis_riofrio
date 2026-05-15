"""
flask seed-data
Genera datos de prueba realistas para la base de datos de Mechita.
Rango de fechas: 11 al 14 de mayo de 2026.
Idempotente: verifica existencia antes de insertar.
"""
import click
from flask.cli import with_appcontext
from datetime import datetime
from werkzeug.security import generate_password_hash
from bson import ObjectId
from database.mongoDb import DatabaseConnection


# ── Fechas de referencia ────────────────────────────────────────────────────
D11 = datetime(2026, 5, 11,  8, 30,  0)
D11b= datetime(2026, 5, 11, 11, 15,  0)
D12 = datetime(2026, 5, 12,  9,  0,  0)
D12b= datetime(2026, 5, 12, 14, 20,  0)
D13 = datetime(2026, 5, 13, 10, 45,  0)
D13b= datetime(2026, 5, 13, 16, 30,  0)
D14 = datetime(2026, 5, 14,  8, 10,  0)
D14b= datetime(2026, 5, 14, 11, 55,  0)


def col(name):
    return DatabaseConnection.get_collection(name)


def echo_ok(msg):   click.echo(click.style(f"  ✔  {msg}", fg="green"))
def echo_skip(msg): click.echo(click.style(f"  –  {msg} (ya existe)", fg="yellow"))
def echo_err(msg):  click.echo(click.style(f"  ✘  {msg}", fg="red"))
def echo_hdr(msg):  click.echo(click.style(f"\n▶ {msg}", bold=True))


# ── Helpers ─────────────────────────────────────────────────────────────────

def _insert_user(users_col, persons_col, identification, first_name, last_name,
                 email, password, role, phone, created_at):
    if persons_col.find_one({"identification": identification}):
        doc = persons_col.find_one({"identification": identification})
        echo_skip(f"Usuario {first_name} {last_name} ({identification})")
        return str(doc["user_id"]) if "user_id" in doc else None
    if users_col.find_one({"email": email}):
        doc = users_col.find_one({"email": email})
        echo_skip(f"Email {email}")
        return str(doc["_id"])
    uid = users_col.insert_one({
        "email": email,
        "password": generate_password_hash(password),
        "role": role,
        "created_at": created_at
    }).inserted_id
    persons_col.insert_one({
        "user_id": str(uid),
        "identification": identification,
        "first_name": first_name,
        "last_name": last_name,
        "phone": phone,
        "photo_path": None,
        "created_at": created_at
    })
    echo_ok(f"Usuario {role}: {first_name} {last_name} → {email}")
    return str(uid)


def _find_user_by_identification(persons_col, identification):
    doc = persons_col.find_one({"identification": identification})
    return str(doc["user_id"]) if doc else None


def _ensure(col_obj, query, doc, label):
    if col_obj.find_one(query):
        echo_skip(label)
        existing = col_obj.find_one(query)
        return str(existing["_id"])
    result = col_obj.insert_one(doc)
    echo_ok(label)
    return str(result.inserted_id)


# ── Comando principal ────────────────────────────────────────────────────────

@click.command("seed-data")
@with_appcontext
def seed_data_command():
    click.echo(click.style("\n══════════════════════════════════════════", bold=True))
    click.echo(click.style("  Mechita — Generación de datos de prueba", bold=True))
    click.echo(click.style("══════════════════════════════════════════\n", bold=True))

    users_col    = col("users")
    persons_col  = col("persons")
    cats_col     = col("categories")
    brands_col   = col("brands")
    models_col   = col("vehicle_models")
    suppliers_col= col("suppliers")
    services_col = col("services")
    parts_col    = col("spare_parts")
    stock_col    = col("stock_movements")
    orders_col   = col("work_orders")
    errors_col   = col("common_errors")
    reviews_col  = col("reviews")

    PWD = "Mechita2026!"

    # ── 1. USUARIOS ──────────────────────────────────────────────────────────
    echo_hdr("1. Usuarios")

    operator_id = _insert_user(
        users_col, persons_col,
        identification="0702818717",
        first_name="Carlos", last_name="Méndez",
        email="carlos.mendez@mechita.com", password=PWD,
        role="operator", phone="0991234567", created_at=D11
    )
    mec1_id = _insert_user(
        users_col, persons_col,
        identification="0703599126",
        first_name="Luis", last_name="Alvarado",
        email="luis.alvarado@mechita.com", password=PWD,
        role="mechanic", phone="0987654321", created_at=D11
    )
    client2_id = _insert_user(
        users_col, persons_col,
        identification="0706457454",
        first_name="María", last_name="García",
        email="maria.garcia@mechita.com", password=PWD,
        role="client", phone="0976543210", created_at=D11
    )
    mec2_id = _insert_user(
        users_col, persons_col,
        identification="0706602265",
        first_name="Pedro", last_name="Suárez",
        email="pedro.suarez@mechita.com", password=PWD,
        role="mechanic", phone="0965432109", created_at=D11
    )
    # Cliente existente con cédula 0705463420
    client1_id = _find_user_by_identification(persons_col, "0705463420")
    if client1_id:
        echo_ok(f"Cliente existente (0705463420) → user_id: {client1_id}")
    else:
        client1_id = _insert_user(
            users_col, persons_col,
            identification="0705463420",
            first_name="Andrés", last_name="Riofrío",
            email="andres.riofrio@mechita.com", password=PWD,
            role="client", phone="0954321098", created_at=D11
        )

    # Admin fallback (por si no se ejecutó seed-admin)
    admin_id_doc = users_col.find_one({"role": "admin"})
    admin_id = str(admin_id_doc["_id"]) if admin_id_doc else operator_id

    # ── 2. CATEGORÍAS ────────────────────────────────────────────────────────
    echo_hdr("2. Categorías")
    cat_data = [
        ("Motor y Transmisión", "Componentes del motor, caja de cambios y embrague"),
        ("Sistema de Frenos", "Pastillas, discos, líquidos y bombas de freno"),
        ("Suspensión y Dirección", "Amortiguadores, rotulas, brazos y dirección"),
        ("Sistema Eléctrico", "Baterías, alternadores, sensores y cableado"),
        ("Filtros y Lubricantes", "Filtros de aceite, aire, combustible y aceites"),
        ("Sistema de Enfriamiento", "Termostatos, bombas de agua y radiadores"),
        ("Escape y Emisiones", "Catalizadores, silenciadores y sensores lambda"),
        ("Carrocería y Accesorios", "Espejos, luces, parachoques y accesorios"),
    ]
    cat_ids = {}
    for name, desc in cat_data:
        cid = _ensure(cats_col, {"name": name},
                      {"name": name, "description": desc, "created_at": D11}, f"Categoría: {name}")
        cat_ids[name] = cid

    # ── 3. MARCAS ────────────────────────────────────────────────────────────
    echo_hdr("3. Marcas")
    brand_data = [
        ("Toyota",    "Fabricante japonés — mayor venta en Ecuador"),
        ("Chevrolet", "General Motors — amplia presencia en mercado ecuatoriano"),
        ("Hyundai",   "Fabricante coreano de gran crecimiento regional"),
        ("Kia",       "Fabricante coreano, popular en segmento económico"),
        ("Ford",      "Fabricante estadounidense, fuerte en pickups"),
        ("Mazda",     "Fabricante japonés, enfocado en eficiencia"),
    ]
    brand_ids = {}
    for name, desc in brand_data:
        bid = _ensure(brands_col, {"name": name},
                      {"name": name, "description": desc, "created_at": D11}, f"Marca: {name}")
        brand_ids[name] = bid

    # ── 4. MODELOS DE VEHÍCULO ───────────────────────────────────────────────
    echo_hdr("4. Modelos de vehículo")
    vm_map = {
        "Toyota": [
            ("Corolla",     "Sedán compacto de alta fiabilidad, motor 1.8 L y 2.0 L gasolina. Uno de los más vendidos en Ecuador."),
            ("Hilux",       "Camioneta 4×4 de trabajo, motor 2.7 L gasolina o 2.4 L diésel. Ideal para terrenos difíciles."),
            ("RAV4",        "SUV familiar con tracción 4×2 y 4×4, motor 2.0 L y 2.5 L híbrido."),
            ("Fortuner",    "SUV 7 plazas sobre plataforma de camioneta, motor 2.7 L gasolina o 2.4 L diésel."),
            ("Yaris",       "Hatchback urbano de bajo consumo, motor 1.5 L gasolina. Popular en ciudades."),
        ],
        "Chevrolet": [
            ("Aveo",        "Sedán económico de gran popularidad en Ecuador, motor 1.5 L gasolina SOHC."),
            ("Sail",        "Sedán compacto de cuatro puertas, motor 1.4 L gasolina. Bajo costo operativo."),
            ("Captiva",     "SUV de 5 o 7 plazas, motor 2.4 L gasolina o 2.0 L diésel turbo."),
            ("D-MAX",       "Camioneta 4×4 de trabajo, motor 2.5 L diésel Turbo VCDi. Muy robusta."),
            ("TrailBlazer", "SUV de tamaño mediano, motor 2.8 L diésel o 3.6 L V6 gasolina."),
        ],
        "Hyundai": [
            ("Tucson",      "SUV compacto con motor 2.0 L gasolina o 1.6 T-GDI turbo. Diseño moderno y eficiente."),
            ("Santa Fe",    "SUV mediano con 5 o 7 plazas, motor 2.4 L o 2.0 T diésel."),
            ("Accent",      "Sedán compacto de bajo costo operativo, motor 1.4 L o 1.6 L gasolina."),
            ("i10",         "Hatchback urbano de 5 puertas, motor 1.0 L o 1.2 L gasolina. Ideal para ciudad."),
        ],
        "Kia": [
            ("Sportage",    "SUV compacto con motor 2.0 L gasolina o 1.6 T-GDI turbo. Gran relación calidad-precio."),
            ("Picanto",     "Hatchback urbano de 5 puertas, motor 1.0 L gasolina. El más pequeño de Kia."),
            ("Rio",         "Sedán o hatchback compacto, motor 1.4 L gasolina. Muy económico en combustible."),
            ("Sorento",     "SUV mediano con 5 o 7 plazas, motor 2.4 L gasolina o 2.2 L diésel turbo."),
        ],
        "Ford": [
            ("EcoSport",    "SUV subcompacto con motor 1.5 L o 2.0 L gasolina. Compacto pero espacioso."),
            ("Ranger",      "Camioneta 4×4 de trabajo, motor 3.2 L diésel 5 cilindros. Ideal para carga."),
            ("Escape",      "SUV familiar, motor 2.0 L EcoBoost turbo o 2.5 L Duratec gasolina."),
        ],
        "Mazda": [
            ("CX-5",        "SUV compacto con motor 2.0 L o 2.5 L SKYACTIV-G. Diseño elegante y eficiente."),
            ("Mazda 3",     "Sedán o hatchback eficiente, motor 2.0 L SKYACTIV-G. Excelente manejo."),
            ("Mazda 6",     "Sedán ejecutivo con motor 2.5 L SKYACTIV-G gasolina. Confort superior."),
        ],
    }
    vm_ids = {}
    for brand_name, models in vm_map.items():
        for (m, desc) in models:
            key = f"{brand_name}::{m}"
            vmid = _ensure(models_col, {"name": m, "brand_id": brand_ids[brand_name]},
                           {"name": m, "description": desc,
                            "brand_id": brand_ids[brand_name], "created_at": D11},
                           f"Modelo: {brand_name} {m}")
            vm_ids[key] = vmid

    # ── 5. PROVEEDORES ───────────────────────────────────────────────────────
    echo_hdr("5. Proveedores")
    sup_data = [
        ("RepuestosTec S.A.",
         "Juan Torres", "042-551234", "ventas@repuestostec.ec", "Av. de las Américas 1450, Guayaquil"),
        ("AutoPartes del Sur Cía. Ltda.",
         "Sandra Mora", "072-234567", "info@autopartesdelsur.com", "Calle Loja 345, Cuenca"),
        ("Distribuidora Nacional de Repuestos",
         "Roberto Vega", "022-890123", "contacto@dnr.ec", "Av. 10 de Agosto 2890, Quito"),
    ]
    sup_ids = {}
    for name, contact, phone, email, address in sup_data:
        sid = _ensure(suppliers_col, {"name": name},
                      {"name": name, "contact": contact, "phone": phone,
                       "email": email, "address": address, "created_at": D11},
                      f"Proveedor: {name}")
        sup_ids[name] = sid

    # ── 6. SERVICIOS ─────────────────────────────────────────────────────────
    echo_hdr("6. Servicios del taller")
    svc_data = [
        ("Cambio de aceite y filtro",     "Cambio de aceite de motor con filtro nuevo. Incluye revisión de niveles.", 25.00),
        ("Alineación de ruedas",          "Corrección del ángulo de las ruedas para conducción segura.", 20.00),
        ("Balanceo de ruedas",            "Balanceo electrónico de 4 ruedas para evitar vibración.", 18.00),
        ("Revisión de frenos",            "Inspección completa del sistema de frenos delantero y trasero.", 30.00),
        ("Cambio de pastillas de freno",  "Reemplazo de pastillas delanteras o traseras. No incluye repuesto.", 45.00),
        ("Mantenimiento general 10 000 km","Cambio de aceite, filtros, revisión de frenos y puntos de lubricación.", 80.00),
        ("Diagnóstico computarizado",     "Lectura de fallas con escáner OBD-II y reporte de códigos.", 25.00),
        ("Revisión del sistema eléctrico","Prueba de batería, alternador, arranque y circuitos principales.", 35.00),
        ("Lavado y desengrase de motor",  "Limpieza profunda del compartimiento del motor a vapor.", 40.00),
        ("Cambio de amortiguadores",      "Reemplazo de amortiguadores delanteros o traseros. No incluye repuesto.", 120.00),
    ]
    svc_ids = {}
    for name, desc, price in svc_data:
        sid = _ensure(services_col, {"name": name},
                      {"name": name, "description": desc, "price": price,
                       "is_active": True, "created_at": D11},
                      f"Servicio: {name} — ${price:.2f}")
        svc_ids[name] = sid

    # ── 7. REPUESTOS ─────────────────────────────────────────────────────────
    echo_hdr("7. Repuestos (inventario)")

    # Estructura: (code, name, description, brand, vm_key, category, supplier,
    #              stock_actual, stock_min, stock_max, precio_compra, precio_venta, ubicacion)
    parts_data = [
        ("REP-0001", "Filtro de aceite Toyota",
         "Filtro de aceite original compatible con Corolla, Yaris y RAV4.",
         "Toyota", "Toyota::Corolla", "Filtros y Lubricantes", "RepuestosTec S.A.",
         25, 5, 50, 3.50, 8.00, "Estante A-01"),
        ("REP-0002", "Pastillas de freno delanteras Chevrolet Aveo",
         "Set de 4 pastillas de freno delanteras para Aveo y Sail.",
         "Chevrolet", "Chevrolet::Aveo", "Sistema de Frenos", "AutoPartes del Sur Cía. Ltda.",
         12, 4, 30, 15.00, 35.00, "Estante B-03"),
        ("REP-0003", "Aceite de motor 10W-40 (1 litro)",
         "Aceite mineral multigrado para motores gasolina y diésel.",
         None, None, "Filtros y Lubricantes", "Distribuidora Nacional de Repuestos",
         40, 10, 80, 4.00, 9.00, "Estante A-02"),
        ("REP-0004", "Correa de distribución Toyota Hilux 2.7",
         "Correa de distribución OEM para motor 2TR-FE de Toyota Hilux.",
         "Toyota", "Toyota::Hilux", "Motor y Transmisión", "RepuestosTec S.A.",
         6, 2, 15, 18.00, 45.00, "Estante C-01"),
        ("REP-0005", "Bujías NGK BKR5E (set x4)",
         "Set de 4 bujías NGK estándar, compatibilidad universal gasolina.",
         None, None, "Motor y Transmisión", "RepuestosTec S.A.",
         20, 5, 40, 8.00, 18.00, "Estante C-02"),
        ("REP-0006", "Filtro de aire Hyundai Tucson 2.0",
         "Filtro de aire de panel para Tucson ix35 y Santa Fe.",
         "Hyundai", "Hyundai::Tucson", "Filtros y Lubricantes", "AutoPartes del Sur Cía. Ltda.",
         15, 4, 30, 6.00, 14.00, "Estante A-03"),
        ("REP-0007", "Amortiguador delantero KYB Excel-G",
         "Amortiguador delantero de gas KYB, compatibilidad múltiple.",
         None, None, "Suspensión y Dirección", "Distribuidora Nacional de Repuestos",
         4, 5, 12, 45.00, 90.00, "Estante D-01"),  # STOCK CRÍTICO (4 < min 5)
        ("REP-0008", "Batería Bosch S4 60Ah",
         "Batería de arranque 12V 60Ah libre de mantenimiento.",
         None, None, "Sistema Eléctrico", "RepuestosTec S.A.",
         5, 2, 10, 65.00, 130.00, "Estante E-01"),
        ("REP-0009", "Termostato 82°C universal",
         "Termostato de cera para motor, apertura a 82°C.",
         None, None, "Sistema de Enfriamiento", "AutoPartes del Sur Cía. Ltda.",
         8, 3, 15, 9.00, 22.00, "Estante F-01"),
        ("REP-0010", "Líquido de frenos DOT4 (500 ml)",
         "Líquido de frenos DOT 4 de alta temperatura.",
         None, None, "Sistema de Frenos", "Distribuidora Nacional de Repuestos",
         18, 5, 35, 3.00, 7.00, "Estante B-01"),
        ("REP-0011", "Rodamiento de rueda delantera",
         "Rodamiento de rueda delantera, compatible con múltiples modelos.",
         None, None, "Suspensión y Dirección", "RepuestosTec S.A.",
         3, 2, 10, 22.00, 55.00, "Estante D-02"),
        ("REP-0012", "Alternador remanufacturado 90A",
         "Alternador remanufacturado 12V 90A, garantía 6 meses.",
         None, None, "Sistema Eléctrico", "Distribuidora Nacional de Repuestos",
         2, 1, 5, 95.00, 180.00, "Estante E-02"),  # STOCK CRÍTICO (2=min+1 pero bajo)
        ("REP-0013", "Bomba de agua universal",
         "Bomba de agua de aluminio con empaque incluido.",
         None, None, "Sistema de Enfriamiento", "AutoPartes del Sur Cía. Ltda.",
         7, 2, 12, 28.00, 65.00, "Estante F-02"),
        ("REP-0014", "Kit de embrague Kia Sportage 2.0",
         "Kit completo: disco, plato y collarín para Sportage 2.0.",
         "Kia", "Kia::Sportage", "Motor y Transmisión", "RepuestosTec S.A.",
         3, 1, 8, 55.00, 120.00, "Estante C-03"),
        ("REP-0015", "Filtro de combustible universal",
         "Filtro de gasolina en línea, rosca 8mm, presión hasta 6 bar.",
         None, None, "Filtros y Lubricantes", "Distribuidora Nacional de Repuestos",
         22, 6, 40, 5.00, 12.00, "Estante A-04"),
    ]

    part_ids = {}
    for (code, name, desc, brand, vm_key, cat, sup,
         stock, s_min, s_max, p_comp, p_venta, ubic) in parts_data:
        if parts_col.find_one({"code": code}):
            echo_skip(f"Repuesto {code}: {name}")
            doc = parts_col.find_one({"code": code})
            part_ids[code] = str(doc["_id"])
            continue
        doc = {
            "code": code,
            "name": name,
            "description": desc,
            "brand_id": brand_ids.get(brand) if brand else None,
            "vehicle_model_id": vm_ids.get(vm_key) if vm_key else None,
            "category_id": cat_ids.get(cat),
            "supplier_id": sup_ids.get(sup),
            "stock_actual": stock,
            "stock_minimo": s_min,
            "stock_maximo": s_max,
            "precio_compra": p_comp,
            "precio_venta": p_venta,
            "ubicacion": ubic,
            "imagen": None,
            "is_active": True,
            "created_at": D11,
        }
        pid = parts_col.insert_one(doc).inserted_id
        part_ids[code] = str(pid)
        echo_ok(f"Repuesto {code}: {name} (stock={stock})")

    # ── 8. MOVIMIENTOS DE STOCK ──────────────────────────────────────────────
    echo_hdr("8. Movimientos de stock")

    if stock_col.count_documents({}) > 0:
        echo_skip("Movimientos de stock (ya existen, se omiten todos)")
    else:
        #
        # Las entradas que explican el stock actual:
        # stock_actual = compras - ventas_directas - descontado_por_ordenes
        #
        entries = [
            # (spare_part_id_key, qty, motive, note, user_id, wo_id, date)
            # ── 11 Mayo — compras iniciales ──
            ("REP-0001", 30, "compra", "Compra inicial — proveedor RepuestosTec", operator_id, None, D11),
            ("REP-0002", 20, "compra", "Compra inicial — AutoPartes del Sur",     operator_id, None, D11),
            ("REP-0003", 50, "compra", "Compra inicial — 50 litros de aceite",    operator_id, None, D11),
            ("REP-0005", 25, "compra", "Compra inicial — bujías NGK",             operator_id, None, D11),
            ("REP-0007",  6, "compra", "Compra inicial — amortiguadores KYB",     operator_id, None, D11),
            ("REP-0009", 10, "compra", "Compra inicial — termostatos",            operator_id, None, D11),
            ("REP-0011",  5, "compra", "Compra inicial — rodamientos",            operator_id, None, D11),
            ("REP-0014",  5, "compra", "Compra inicial — kits embrague Kia",      operator_id, None, D11),
            # ── 12 Mayo — compras adicionales ──
            ("REP-0004", 10, "compra", "Compra — correas de distribución",        operator_id, None, D12),
            ("REP-0006", 20, "compra", "Compra — filtros de aire Hyundai",        operator_id, None, D12),
            ("REP-0010", 25, "compra", "Compra — líquido de frenos DOT4",         operator_id, None, D12),
            ("REP-0012",  3, "compra", "Compra — alternadores remanufacturados",  operator_id, None, D12),
            ("REP-0015", 25, "compra", "Compra — filtros de combustible",         operator_id, None, D12),
            # ── 13 Mayo ──
            ("REP-0008",  8, "compra", "Compra — baterías Bosch",                 operator_id, None, D13),
            ("REP-0013", 10, "compra", "Compra — bombas de agua",                 operator_id, None, D13),
        ]

        exits = [
            # Salidas por OT-001 (finalizado 11 mayo)
            ("REP-0001",  2, "orden_trabajo", "OT #1 — Toyota Corolla ABC-1234", operator_id, "__OT1__", D11b),
            ("REP-0003",  3, "orden_trabajo", "OT #1 — Toyota Corolla ABC-1234", operator_id, "__OT1__", D11b),
            ("REP-0005",  1, "orden_trabajo", "OT #1 — Toyota Corolla ABC-1234", operator_id, "__OT1__", D11b),
            # Ventas directas 11 mayo
            ("REP-0003",  2, "venta_directa", "Venta directa mostrador",          operator_id, None, D11b),
            # Ventas directas 12 mayo
            ("REP-0001",  3, "venta_directa", "Venta directa mostrador",          operator_id, None, D12),
            ("REP-0003",  5, "venta_directa", "Venta directa mostrador",          operator_id, None, D12),
            ("REP-0005",  4, "venta_directa", "Venta directa mostrador",          operator_id, None, D12),
            ("REP-0009",  2, "venta_directa", "Venta directa — termostato",       operator_id, None, D12b),
            ("REP-0014",  2, "venta_directa", "Venta directa — kit embrague Kia", operator_id, None, D12b),
            # Ventas directas 13 mayo
            ("REP-0002",  4, "venta_directa", "Venta directa — pastillas freno",  operator_id, None, D13),
            ("REP-0010",  7, "venta_directa", "Venta directa — líquido frenos",   operator_id, None, D13),
            ("REP-0006",  5, "venta_directa", "Venta directa — filtros aire",     operator_id, None, D13b),
            ("REP-0002",  4, "venta_directa", "Venta directa — pastillas freno",  operator_id, None, D13b),
            # Salidas por OT-004 (finalizado 13 mayo)
            ("REP-0004",  4, "orden_trabajo", "OT #4 — Toyota Hilux GHI-3456",   operator_id, "__OT4__", D13b),
            ("REP-0007",  2, "orden_trabajo", "OT #4 — Toyota Hilux GHI-3456",   operator_id, "__OT4__", D13b),
            ("REP-0011",  2, "orden_trabajo", "OT #4 — Toyota Hilux GHI-3456",   operator_id, "__OT4__", D13b),
            # Ventas directas 14 mayo
            ("REP-0008",  3, "venta_directa", "Venta directa — batería",          operator_id, None, D14),
            ("REP-0012",  1, "venta_directa", "Venta directa — alternador",       operator_id, None, D14),
            ("REP-0013",  3, "venta_directa", "Venta directa — bomba de agua",    operator_id, None, D14),
            ("REP-0015",  3, "venta_directa", "Venta directa — filtro combustible",operator_id,None, D14b),
        ]

        for code, qty, motive, note, uid, wo_id, dt in entries:
            stock_col.insert_one({
                "spare_part_id": part_ids[code],
                "movement_type": "entrada",
                "quantity": qty,
                "motive": motive,
                "note": note,
                "user_id": uid,
                "work_order_id": None,
                "attachment_path": None,
                "created_at": dt,
            })
        echo_ok(f"Entradas de stock: {len(entries)} movimientos")

        for code, qty, motive, note, uid, wo_id_placeholder, dt in exits:
            stock_col.insert_one({
                "spare_part_id": part_ids[code],
                "movement_type": "salida",
                "quantity": qty,
                "motive": motive,
                "note": note,
                "user_id": uid,
                "work_order_id": None,   # se actualiza después con el ID real
                "attachment_path": None,
                "created_at": dt,
            })
        echo_ok(f"Salidas de stock: {len(exits)} movimientos")

    # ── 9. INGRESOS DE TALLER ───────────────────────────────────────────────
    echo_hdr("9. Ingresos de taller")

    if orders_col.count_documents({}) > 0:
        echo_skip("Órdenes de trabajo (ya existen, se omiten todas)")
    else:
        def _next_number():
            doc = orders_col.find_one(sort=[("number", -1)])
            return (doc["number"] + 1) if doc else 1

        # ── OT-001: FINALIZADO — 11 mayo ─────────────────────────────────
        ot1_parts = [
            {"spare_part_id": part_ids["REP-0001"], "spare_part_name": "Filtro de aceite Toyota",
             "quantity": 2, "unit_price": 8.00, "subtotal": 16.00},
            {"spare_part_id": part_ids["REP-0003"], "spare_part_name": "Aceite de motor 10W-40 (1 litro)",
             "quantity": 3, "unit_price": 9.00, "subtotal": 27.00},
            {"spare_part_id": part_ids["REP-0005"], "spare_part_name": "Bujías NGK BKR5E (set x4)",
             "quantity": 1, "unit_price": 18.00, "subtotal": 18.00},
        ]
        ot1_labor = 25.00
        ot1_total = sum(p["subtotal"] for p in ot1_parts) + ot1_labor   # 86.00
        ot1_id = orders_col.insert_one({
            "number": _next_number(),
            "client_id": client1_id,
            "vehicle_brand": "Toyota",
            "vehicle_model": "Corolla",
            "vehicle_plate": "ABC-1234",
            "vehicle_year": "2018",
            "parts": ot1_parts,
            "labor_cost": ot1_labor,
            "total": ot1_total,
            "status": "entregado",
            "operator_id": operator_id,
            "mechanic_id": mec1_id,
            "notes": "Mantenimiento preventivo 10 000 km. Vehículo en buen estado general.",
            "vehicle_photos": [],
            "created_at": D11,
            "updated_at": D11b,
        }).inserted_id
        echo_ok(f"OT #1 — Toyota Corolla ABC-1234 (FINALIZADO) — Total: ${ot1_total:.2f}")

        # Vincular salidas de stock de OT1
        stock_col.update_many(
            {"note": {"$regex": "OT #1"}, "movement_type": "salida"},
            {"$set": {"work_order_id": str(ot1_id)}}
        )

        # ── OT-002: EN REVISIÓN — 12 mayo ───────────────────────────────
        ot2_parts = [
            {"spare_part_id": part_ids["REP-0002"], "spare_part_name": "Pastillas de freno delanteras Chevrolet Aveo",
             "quantity": 1, "unit_price": 35.00, "subtotal": 35.00},
            {"spare_part_id": part_ids["REP-0010"], "spare_part_name": "Líquido de frenos DOT4 (500 ml)",
             "quantity": 2, "unit_price": 7.00, "subtotal": 14.00},
        ]
        ot2_labor = 30.00
        ot2_total = sum(p["subtotal"] for p in ot2_parts) + ot2_labor  # 79.00
        ot2_id = orders_col.insert_one({
            "number": _next_number(),
            "client_id": client2_id,
            "vehicle_brand": "Chevrolet",
            "vehicle_model": "Aveo",
            "vehicle_plate": "XYZ-5678",
            "vehicle_year": "2015",
            "parts": ot2_parts,
            "labor_cost": ot2_labor,
            "total": ot2_total,
            "status": "presupuesto",
            "operator_id": operator_id,
            "mechanic_id": mec2_id,
            "notes": "Cliente reporta vibración al frenar y chirrido en rueda delantera derecha.",
            "vehicle_photos": [],
            "created_at": D12,
            "updated_at": D12b,
        }).inserted_id
        echo_ok(f"OT #2 — Chevrolet Aveo XYZ-5678 (EN REVISIÓN) — Total: ${ot2_total:.2f}")

        # ── OT-003: RESULTADO DEL CHEQUEO — 13 mayo ─────────────────────
        ot3_parts = [
            {"spare_part_id": part_ids["REP-0006"], "spare_part_name": "Filtro de aire Hyundai Tucson 2.0",
             "quantity": 1, "unit_price": 14.00, "subtotal": 14.00},
            {"spare_part_id": part_ids["REP-0009"], "spare_part_name": "Termostato 82°C universal",
             "quantity": 1, "unit_price": 22.00, "subtotal": 22.00},
        ]
        ot3_labor = 45.00
        ot3_total = sum(p["subtotal"] for p in ot3_parts) + ot3_labor  # 81.00
        ot3_id = orders_col.insert_one({
            "number": _next_number(),
            "client_id": client1_id,
            "vehicle_brand": "Hyundai",
            "vehicle_model": "Tucson",
            "vehicle_plate": "DEF-9012",
            "vehicle_year": "2020",
            "parts": ot3_parts,
            "labor_cost": ot3_labor,
            "total": ot3_total,
            "status": "aprobado",
            "operator_id": operator_id,
            "mechanic_id": mec1_id,
            "notes": "Motor sobrecalentando. Se detectó termostato defectuoso y filtro de aire saturado.",
            "vehicle_photos": [],
            "created_at": D13,
            "updated_at": D13,
        }).inserted_id
        echo_ok(f"OT #3 — Hyundai Tucson DEF-9012 (RESULTADO CHEQUEO) — Total: ${ot3_total:.2f}")

        # ── OT-004: FINALIZADO — 13 mayo ─────────────────────────────────
        ot4_parts = [
            {"spare_part_id": part_ids["REP-0004"], "spare_part_name": "Correa de distribución Toyota Hilux 2.7",
             "quantity": 4, "unit_price": 45.00, "subtotal": 180.00},
            {"spare_part_id": part_ids["REP-0007"], "spare_part_name": "Amortiguador delantero KYB Excel-G",
             "quantity": 2, "unit_price": 90.00, "subtotal": 180.00},
            {"spare_part_id": part_ids["REP-0011"], "spare_part_name": "Rodamiento de rueda delantera",
             "quantity": 2, "unit_price": 55.00, "subtotal": 110.00},
        ]
        ot4_labor = 120.00
        ot4_total = sum(p["subtotal"] for p in ot4_parts) + ot4_labor  # 590.00
        ot4_id = orders_col.insert_one({
            "number": _next_number(),
            "client_id": client2_id,
            "vehicle_brand": "Toyota",
            "vehicle_model": "Hilux",
            "vehicle_plate": "GHI-3456",
            "vehicle_year": "2016",
            "parts": ot4_parts,
            "labor_cost": ot4_labor,
            "total": ot4_total,
            "status": "entregado",
            "operator_id": operator_id,
            "mechanic_id": mec1_id,
            "notes": "Mantenimiento mayor: cambio de distribución, amortiguadores y rodamientos. Vehículo con 95 000 km.",
            "vehicle_photos": [],
            "created_at": D13,
            "updated_at": D13b,
        }).inserted_id
        echo_ok(f"OT #4 — Toyota Hilux GHI-3456 (FINALIZADO) — Total: ${ot4_total:.2f}")

        # Vincular salidas de stock de OT4
        stock_col.update_many(
            {"note": {"$regex": "OT #4"}, "movement_type": "salida"},
            {"$set": {"work_order_id": str(ot4_id)}}
        )

        # ── OT-005: INGRESADO — 14 mayo ──────────────────────────────────
        ot5_id = orders_col.insert_one({
            "number": _next_number(),
            "client_id": client2_id,
            "vehicle_brand": "Kia",
            "vehicle_model": "Sportage",
            "vehicle_plate": "JKL-7890",
            "vehicle_year": "2019",
            "parts": [],
            "labor_cost": 0.0,
            "total": 0.0,
            "status": "diagnostico",
            "operator_id": operator_id,
            "mechanic_id": mec2_id,
            "notes": "Vehículo ingresa por diagnóstico: luces de tablero encendidas (check engine y ABS). Pendiente revisión.",
            "vehicle_photos": [],
            "created_at": D14,
            "updated_at": D14,
        }).inserted_id
        echo_ok(f"OT #5 — Kia Sportage JKL-7890 (EN DIAGNÓSTICO) — Total: $0.00")

        # ── OT-006: RECEPCIÓN — 14 mayo (segunda entrada del día) ────────
        ot6_id = orders_col.insert_one({
            "number": _next_number(),
            "client_id": client1_id,
            "vehicle_brand": "Mazda",
            "vehicle_model": "Mazda 3",
            "vehicle_plate": "MNO-2345",
            "vehicle_year": "2022",
            "parts": [],
            "labor_cost": 0.0,
            "total": 0.0,
            "status": "recepcion",
            "operator_id": operator_id,
            "mechanic_id": None,
            "notes": "Ingresa para alineación y balanceo. Sin mecánico asignado aún.",
            "vehicle_photos": [],
            "created_at": D14b,
            "updated_at": D14b,
        }).inserted_id
        echo_ok(f"OT #6 — Mazda 3 MNO-2345 (RECEPCIÓN, sin mecánico) — Total: $0.00")

    # ── 10. ERRORES COMUNES DE VEHÍCULOS ────────────────────────────────────
    echo_hdr("10. Errores comunes de vehículos")

    if errors_col.count_documents({}) > 0:
        echo_skip("Errores comunes (ya existen)")
    else:
        common_errors_data = [
            # Toyota Corolla
            {
                "brand_id": brand_ids["Toyota"],
                "vehicle_model_id": vm_ids["Toyota::Corolla"],
                "year_from": 2014, "year_to": 2019,
                "title": "Falla en sensor de posición del cigüeñal",
                "description": "Síntoma: motor tirita o apaga inesperadamente. Causa: sensor CKP deteriorado por calor. Solución: reemplazar sensor y limpiar conector.",
                "severity": "alta", "created_at": D11,
            },
            {
                "brand_id": brand_ids["Toyota"],
                "vehicle_model_id": vm_ids["Toyota::Corolla"],
                "year_from": 2010, "year_to": 2018,
                "title": "Consumo excesivo de aceite",
                "description": "El motor consume más de 1 litro cada 1000 km. Causa: sellos de válvulas y anillos desgastados. Verificar nivel cada 2000 km y realizar prueba de consumo.",
                "severity": "media", "created_at": D11,
            },
            # Toyota Hilux
            {
                "brand_id": brand_ids["Toyota"],
                "vehicle_model_id": vm_ids["Toyota::Hilux"],
                "year_from": 2012, "year_to": 2020,
                "title": "Vibración en volante a velocidades altas",
                "description": "Vibración entre 80-110 km/h. Generalmente causado por ruedas desbalanceadas o desgaste irregular de neumáticos. Revisar balanceo, rotación y estado de amortiguadores.",
                "severity": "media", "created_at": D11,
            },
            {
                "brand_id": brand_ids["Toyota"],
                "vehicle_model_id": vm_ids["Toyota::Hilux"],
                "year_from": 2015, "year_to": None,
                "title": "Ruido en diferencial trasero",
                "description": "Ruido de zumbido o chasquido en marcha. Revisar nivel y calidad del aceite del diferencial. Si persiste, posible desgaste de engranajes del diferencial.",
                "severity": "alta", "created_at": D12,
            },
            # Chevrolet Aveo
            {
                "brand_id": brand_ids["Chevrolet"],
                "vehicle_model_id": vm_ids["Chevrolet::Aveo"],
                "year_from": 2006, "year_to": 2018,
                "title": "Falla en sensor MAP (presión múltiple)",
                "description": "Check engine encendido con código P0106 o P0107. Motor inestable en ralentí. Limpiar o reemplazar sensor MAP. Verificar manguera de vacío.",
                "severity": "media", "created_at": D11,
            },
            {
                "brand_id": brand_ids["Chevrolet"],
                "vehicle_model_id": vm_ids["Chevrolet::Aveo"],
                "year_from": 2006, "year_to": 2015,
                "title": "Desgaste prematuro de pastillas de freno",
                "description": "Las pastillas traseras se desgastan antes que las delanteras. Revisar calibradores traseros por arrastre. Lubricar guías con grasa de silicona.",
                "severity": "baja", "created_at": D12,
            },
            # Hyundai Tucson
            {
                "brand_id": brand_ids["Hyundai"],
                "vehicle_model_id": vm_ids["Hyundai::Tucson"],
                "year_from": 2015, "year_to": 2021,
                "title": "Fuga en empaque de tapa de válvulas",
                "description": "Goteo de aceite sobre el múltiple de escape, puede generar humo y olor a quemado. Reemplazar empaque de tapa de válvulas. Preventivo cada 80 000 km.",
                "severity": "media", "created_at": D13,
            },
            # Kia Sportage
            {
                "brand_id": brand_ids["Kia"],
                "vehicle_model_id": vm_ids["Kia::Sportage"],
                "year_from": 2016, "year_to": None,
                "title": "Vibración al acelerar desde parado",
                "description": "Tremblor en arranque fuerte. Revisión de soporte o cojinetes del motor. También puede ser desgaste en puntas de eje. Hacer diagnóstico de transmisión.",
                "severity": "media", "created_at": D13,
            },
            # Mazda 3
            {
                "brand_id": brand_ids["Mazda"],
                "vehicle_model_id": vm_ids["Mazda::Mazda 3"],
                "year_from": 2014, "year_to": 2019,
                "title": "Ruido de traqueteo al arrancar en frío",
                "description": "Ruido metálico los primeros 2-5 segundos después de arrancar. Causa: tensionador de cadena de distribución con desgaste. Revisar nivel de aceite y calidad. Cambiar tensionador si persiste.",
                "severity": "alta", "created_at": D14,
            },
        ]
        errors_col.insert_many(common_errors_data)
        echo_ok(f"Errores comunes: {len(common_errors_data)} registros")

    # ── 11. RESEÑAS DE CATÁLOGO ──────────────────────────────────────────────
    echo_hdr("11. Reseñas de catálogo")

    if reviews_col.count_documents({}) > 0:
        echo_skip("Reseñas (ya existen)")
    else:
        reviews_data = [
            # Reseñas de repuestos
            {
                "subject_type": "part", "subject_id": part_ids["REP-0001"],
                "user_id": client1_id, "user_name": "Andrés Riofrío",
                "rating": 5, "comment": "Filtro original de excelente calidad. Perfecto para mi Corolla, sin fugas.",
                "created_at": D12,
            },
            {
                "subject_type": "part", "subject_id": part_ids["REP-0001"],
                "user_id": client2_id, "user_name": "María García",
                "rating": 4, "comment": "Buen filtro, fácil de instalar. Precio justo.",
                "created_at": D13,
            },
            {
                "subject_type": "part", "subject_id": part_ids["REP-0003"],
                "user_id": client1_id, "user_name": "Andrés Riofrío",
                "rating": 4, "comment": "Aceite de buena viscosidad. El motor quedó más silencioso después del cambio.",
                "created_at": D13,
            },
            {
                "subject_type": "part", "subject_id": part_ids["REP-0005"],
                "user_id": client2_id, "user_name": "María García",
                "rating": 5, "comment": "Bujías NGK de siempre. Encendido perfecto, noté diferencia en consumo de combustible.",
                "created_at": D14,
            },
            {
                "subject_type": "part", "subject_id": part_ids["REP-0002"],
                "user_id": client2_id, "user_name": "María García",
                "rating": 4, "comment": "Pastillas de buena calidad, sin chirrido. Frenado muy mejorado.",
                "created_at": D14,
            },
            # Reseñas de servicios
            {
                "subject_type": "service", "subject_id": svc_ids["Cambio de aceite y filtro"],
                "user_id": client1_id, "user_name": "Andrés Riofrío",
                "rating": 5, "comment": "Servicio rápido y profesional. En menos de 30 minutos listo.",
                "created_at": D12,
            },
            {
                "subject_type": "service", "subject_id": svc_ids["Cambio de aceite y filtro"],
                "user_id": client2_id, "user_name": "María García",
                "rating": 5, "comment": "Excelente atención, muy limpios con el trabajo.",
                "created_at": D13,
            },
            {
                "subject_type": "service", "subject_id": svc_ids["Diagnóstico computarizado"],
                "user_id": client1_id, "user_name": "Andrés Riofrío",
                "rating": 4, "comment": "El reporte de diagnóstico fue muy completo y explicaron todo en detalle.",
                "created_at": D14,
            },
            {
                "subject_type": "service", "subject_id": svc_ids["Revisión de frenos"],
                "user_id": client2_id, "user_name": "María García",
                "rating": 5, "comment": "Detectaron el problema rápidamente. Muy recomendado.",
                "created_at": D13,
            },
            {
                "subject_type": "service", "subject_id": svc_ids["Alineación de ruedas"],
                "user_id": client1_id, "user_name": "Andrés Riofrío",
                "rating": 4, "comment": "Buen trabajo, el auto quedó estable en carretera.",
                "created_at": D14,
            },
        ]
        reviews_col.insert_many(reviews_data)
        echo_ok(f"Reseñas: {len(reviews_data)} registros")

    # ── Resumen ──────────────────────────────────────────────────────────────
    click.echo(click.style("\n══════════════════════════════════════════", bold=True))
    click.echo(click.style("  ✔  Datos de prueba generados con éxito", fg="green", bold=True))
    click.echo()
    click.echo(f"  Credencial de acceso para todos los usuarios nuevos:")
    click.echo(click.style(f"  Contraseña: {PWD}", fg="cyan"))
    click.echo()
    click.echo("  Usuarios creados:")
    click.echo("    carlos.mendez@mechita.com   → Operador")
    click.echo("    luis.alvarado@mechita.com   → Mecánico")
    click.echo("    pedro.suarez@mechita.com    → Mecánico")
    click.echo("    maria.garcia@mechita.com    → Cliente")
    click.echo(click.style("══════════════════════════════════════════\n", bold=True))
