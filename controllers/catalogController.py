from flask import render_template, request, Blueprint
from services.sparePartService import SparePartService
from services.serviceService import ServiceService
from services.brandService import BrandService
from services.categoryService import CategoryService
from services.vehicleModelService import VehicleModelService

catalog_bp = Blueprint('catalog', __name__, url_prefix='/catalog')

@catalog_bp.route('/', methods=['GET'])
def index():
    page = int(request.args.get('page', 1))
    search = request.args.get('search', '').strip() or None
    category_id = request.args.get('category_id', '').strip() or None
    brand_id = request.args.get('brand_id', '').strip() or None

    result = SparePartService.get_paginated(
        page=page, per_page=12,
        search=search, category_id=category_id, brand_id=brand_id
    )
    services = ServiceService.get_all_active().get("services", [])
    categories = CategoryService.get_all().get("categories", [])
    brands = BrandService.get_all().get("brands", [])

    parts = result.get("parts", [])
    brands_map = {b.id: b.name for b in brands}
    categories_map = {c.id: c.name for c in categories}

    return render_template('/views/catalog/index.html',
                           parts=parts,
                           services=services,
                           categories=categories,
                           brands=brands,
                           brands_map=brands_map,
                           categories_map=categories_map,
                           total=result.get("total", 0),
                           page=page,
                           total_pages=result.get("total_pages", 1),
                           filter_search=search or '',
                           filter_category=category_id or '',
                           filter_brand=brand_id or '')
