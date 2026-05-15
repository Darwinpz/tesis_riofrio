from flask import Flask
from flask_wtf.csrf import CSRFProtect
from database.mongoDb import DatabaseConnection
from controllers.indexController import index_bp
from controllers.userController import user_bp
from controllers.errorController import error_bp
from controllers.dashboardController import dashboard_bp
from controllers.adminController import admin_bp
from controllers.categoryController import category_bp
from controllers.supplierController import supplier_bp
from controllers.sparePartController import spare_part_bp
from controllers.stockController import stock_bp
from controllers.workOrderController import work_order_bp
from controllers.brandController import brand_bp
from controllers.vehicleModelController import vehicle_model_bp
from controllers.serviceController import service_bp
from controllers.catalogController import catalog_bp
from controllers.commonErrorController import common_error_bp
from dotenv import load_dotenv
from commands.adminCommands import seed_admin_command
from commands.seedDataCommands import seed_data_command
import os

load_dotenv()

app = Flask(__name__, static_folder='public', static_url_path='')

app.secret_key = os.getenv("SECRET_KEY")

CSRFProtect(app)

with app.app_context():
    DatabaseConnection.initialize()

# -- Control de Cache --
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

# -- Rutas BluePrint --
app.register_blueprint(error_bp)
app.register_blueprint(index_bp)
app.register_blueprint(user_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(category_bp)
app.register_blueprint(supplier_bp)
app.register_blueprint(spare_part_bp)
app.register_blueprint(stock_bp)
app.register_blueprint(work_order_bp)
app.register_blueprint(brand_bp)
app.register_blueprint(vehicle_model_bp)
app.register_blueprint(service_bp)
app.register_blueprint(catalog_bp)
app.register_blueprint(common_error_bp)

# -- Comandos CLI --
app.cli.add_command(seed_admin_command)
app.cli.add_command(seed_data_command)

# -- Ejecución --
if __name__ == '__main__':
    app.run(host=os.getenv("HOST"), port=os.getenv("PORT"), debug=os.getenv("DEBUG"))
