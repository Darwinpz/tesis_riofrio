from flask import render_template, Blueprint
from repositories.stockMovementRepository import StockMovementRepository
from repositories.sparePartRepository import SparePartRepository

index_bp = Blueprint("index", __name__, url_prefix='/')

@index_bp.route('/', methods=['GET'])
def indexRoute():
    top_sellers = []
    try:
        top_ids = StockMovementRepository.find_top_seller_ids(limit=6)
        for item in top_ids:
            part = SparePartRepository.find_by_id(item["_id"])
            if part and part.is_active:
                part.total_sold = item["total_sold"]
                top_sellers.append(part)
    except Exception:
        pass
    return render_template('/views/index.html', top_sellers=top_sellers)

@index_bp.route('/about', methods=['GET'])
def aboutRoute():
    return render_template('/views/about.html')
