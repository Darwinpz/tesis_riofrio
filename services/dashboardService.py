from typing import Dict
from datetime import datetime, timedelta
from repositories.sparePartRepository import SparePartRepository
from repositories.stockMovementRepository import StockMovementRepository
from repositories.workOrderRepository import WorkOrderRepository

class DashboardService:

    @staticmethod
    def get_stats() -> Dict:
        try:
            total_parts = SparePartRepository.count_active()
            critical_count = SparePartRepository.count_critical()
            movements_today = StockMovementRepository.count_today()
            active_orders = WorkOrderRepository.count_active()
            critical_parts = SparePartRepository.find_critical_stock()

            return {
                "success": True,
                "total_parts": total_parts,
                "critical_count": critical_count,
                "movements_today": movements_today,
                "active_orders": active_orders,
                "critical_parts": critical_parts
            }
        except Exception as e:
            return {"success": False, "message": f"Error al obtener estadísticas: {e}",
                    "total_parts": 0, "critical_count": 0, "movements_today": 0,
                    "active_orders": 0, "critical_parts": []}

    @staticmethod
    def get_chart_data(days: int = 7) -> Dict:
        try:
            raw = StockMovementRepository.count_by_day(days)
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            labels = []
            entradas = []
            salidas = []
            for i in range(days - 1, -1, -1):
                day = today - timedelta(days=i)
                labels.append(day.strftime("%d/%m"))
                day_data = {"entrada": 0, "salida": 0}
                for item in raw:
                    gid = item["_id"]
                    if (gid["year"] == day.year and gid["month"] == day.month
                            and gid["day"] == day.day):
                        day_data[gid["type"]] = item["count"]
                entradas.append(day_data["entrada"])
                salidas.append(day_data["salida"])

            return {"success": True, "labels": labels, "entradas": entradas, "salidas": salidas}
        except Exception as e:
            return {"success": False, "message": f"Error al obtener datos del gráfico: {e}",
                    "labels": [], "entradas": [], "salidas": []}
