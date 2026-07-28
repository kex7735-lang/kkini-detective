from db_manager import FoodDBManager
from nlu_parser import NaturalLanguageParser

class NutritionCalculator:
    def __init__(self):
        self.nlu = NaturalLanguageParser()
        self.db = FoodDBManager()
        
        # 💡 [핵심 강화] 한국인 맞춤형 초정밀 단위 사전
        self.unit_to_gram = {
            "공기": 210, "개": 50, "인분": 200, "그램": 1, "g": 1, "ml": 1,
            "마리": 800, "조각": 100,
            "대접": 400, "국그릇": 300,    # 국/탕/면류
            "컵": 200, "잔": 150,          # 물/음료류
            "병": 360, "캔": 350,          # 주류/음료류 (소주 1병 기준)
            "근": 600, "모": 300,          # 정육/두부
            "숟가락": 15, "스푼": 15,      # 조미료/소스류
            "봉지": 120                    # 라면/과자류
        }

    def process_meal_record(self, text: str) -> dict:
        parsed_data = self.nlu.parse_meal(text)
        if not parsed_data or not parsed_data.get("items"):
            return {"status": "error", "message": "음식 정보를 추출하지 못했습니다."}

        report = {
            "status": "success",
            "original_text": text,
            "total_nutrition": {"칼로리": 0, "탄수화물": 0, "단백질": 0, "지방": 0},
            "details": []
        }

        for item in parsed_data["items"]:
            food_name = item["food_name"]
            quantity = item["quantity"]
            unit = item["unit"]
            
            search_results = self.db.search_by_name(food_name)
            
            if not search_results:
                report["details"].append({
                    "food_name": food_name,
                    "status": "not_found",
                    "message": "DB에서 해당 음식을 찾을 수 없습니다."
                })
                continue
                
            db_food = search_results[0]
            
            gram_multiplier = self.unit_to_gram.get(unit, 100)
            total_weight_g = quantity * gram_multiplier
            
            base_weight = db_food["1회제공량(g)"]
            ratio = total_weight_g / base_weight if base_weight > 0 else 0
            
            calc_kcal = round(db_food["에너지(kcal)"] * ratio, 1)
            calc_carbs = round(db_food["탄수화물(g)"] * ratio, 1)
            calc_protein = round(db_food["단백질(g)"] * ratio, 1)
            calc_fat = round(db_food["지방(g)"] * ratio, 1)
            
            report["details"].append({
                "food_name": db_food["식품명"],
                "input_name": food_name,
                "섭취량": f"{quantity}{unit} ({total_weight_g}g)",
                "nutrition": {
                    "칼로리": calc_kcal, "탄수화물": calc_carbs, 
                    "단백질": calc_protein, "지방": calc_fat
                }
            })
            
            report["total_nutrition"]["칼로리"] += calc_kcal
            report["total_nutrition"]["탄수화물"] += calc_carbs
            report["total_nutrition"]["단백질"] += calc_protein
            report["total_nutrition"]["지방"] += calc_fat

        for key in report["total_nutrition"]:
            report["total_nutrition"][key] = round(report["total_nutrition"][key], 1)

        return report