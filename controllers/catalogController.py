from flask import render_template, request, redirect, url_for, Blueprint, flash, session
from services.sparePartService import SparePartService
from services.serviceService import ServiceService
from services.brandService import BrandService
from services.categoryService import CategoryService
from services.vehicleModelService import VehicleModelService
from services.reviewService import ReviewService
from repositories.userRepository import UserRepository
from utils.authDecorator import login_required

catalog_bp = Blueprint('catalog', __name__, url_prefix='/catalog')


def _get_user():
    user_id = session.get("user_id")
    return UserRepository.find_by_id(user_id) if user_id else None


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


@catalog_bp.route('/parts/<part_id>', methods=['GET'])
def part_detail(part_id):
    result = SparePartService.get_by_id(part_id)
    if not result["success"]:
        flash("Repuesto no encontrado", 'danger')
        return redirect(url_for('catalog.index'))

    part = result["part"]
    brands = BrandService.get_all().get("brands", [])
    categories = CategoryService.get_all().get("categories", [])
    brand = next((b for b in brands if b.id == part.brand_id), None)
    category = next((c for c in categories if c.id == part.category_id), None)

    review_data = ReviewService.get_for_subject("part", part_id)
    current_user = _get_user()
    user_review = None
    if current_user:
        user_review = ReviewService.get_user_review(current_user.id, "part", part_id)

    return render_template('/views/catalog/part_detail.html',
                           part=part, brand=brand, category=category,
                           reviews=review_data["reviews"],
                           stats=review_data["stats"],
                           user_review=user_review,
                           current_user=current_user)


@catalog_bp.route('/parts/<part_id>/review', methods=['POST'])
@login_required
def part_review(part_id):
    current_user = _get_user()
    if not current_user:
        flash("Debes iniciar sesión para dejar una reseña", 'warning')
        return redirect(url_for('catalog.part_detail', part_id=part_id))

    try:
        rating = int(request.form.get('rating', 0))
    except (ValueError, TypeError):
        rating = 0
    comment = request.form.get('comment', '').strip()
    result = ReviewService.submit("part", part_id, current_user.id,
                                  current_user.first_name + " " + current_user.last_name,
                                  rating, comment)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('catalog.part_detail', part_id=part_id))


@catalog_bp.route('/services/<service_id>', methods=['GET'])
def service_detail(service_id):
    result = ServiceService.get_by_id(service_id)
    if not result["success"]:
        flash("Servicio no encontrado", 'danger')
        return redirect(url_for('catalog.index'))

    service = result["service"]
    review_data = ReviewService.get_for_subject("service", service_id)
    current_user = _get_user()
    user_review = None
    if current_user:
        user_review = ReviewService.get_user_review(current_user.id, "service", service_id)

    return render_template('/views/catalog/service_detail.html',
                           service=service,
                           reviews=review_data["reviews"],
                           stats=review_data["stats"],
                           user_review=user_review,
                           current_user=current_user)


@catalog_bp.route('/services/<service_id>/review', methods=['POST'])
@login_required
def service_review(service_id):
    current_user = _get_user()
    if not current_user:
        flash("Debes iniciar sesión para dejar una reseña", 'warning')
        return redirect(url_for('catalog.service_detail', service_id=service_id))

    try:
        rating = int(request.form.get('rating', 0))
    except (ValueError, TypeError):
        rating = 0
    comment = request.form.get('comment', '').strip()
    result = ReviewService.submit("service", service_id, current_user.id,
                                  current_user.first_name + " " + current_user.last_name,
                                  rating, comment)
    flash(result["message"], 'success' if result["success"] else 'danger')
    return redirect(url_for('catalog.service_detail', service_id=service_id))
