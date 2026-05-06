from flask import render_template, Blueprint

index_bp = Blueprint("index", __name__, url_prefix='/')

@index_bp.route('/', methods=['GET'])
def indexRoute():
    return render_template('/views/index.html')

@index_bp.route('/about', methods=['GET'])
def aboutRoute():
    return render_template('/views/about.html')
