from flask import render_template, Blueprint
from services.dashboardService import DashboardService
from utils.authDecorator import role_required

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/', methods=['GET'])
@role_required('admin', 'operator')
def index():
    stats = DashboardService.get_stats()
    chart = DashboardService.get_chart_data(days=7)
    return render_template('/views/dashboard/index.html', stats=stats, chart=chart)
