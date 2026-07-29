from nlu_parser import NaturalLanguageParser
from db_manager import FoodDBManager

class NutritionCalculator:
    def __init__(self):
        self.nlu = NaturalLanguageParser()
        self.db = FoodDBManager()

    def process_meal_record(self, text: str) -> dict:
        extracted = self.nlu.parse_meal(text)
        
        if not extracted["items"]:
            return {"status": "error", "message": "문장에서 음식 정보를 추출하지 못했습니다."}

        details = []
        # 혹시 모를 UI 에러를 방지하기 위해 기본 총합 형태는 남겨둡니다. (실제 총합은 탐정이 계산합니다)
        total_nutrition = {"칼로리": 0, "단백질": 0, "지방": 0, "탄수화물": 0}

        for item in extracted["items"]:
            # DB에서 찾아온 최대 5명의 용의자 명단
            db_results = self.db.search_by_name(item["search_keywords"])
            
            if not db_results:
                # 엑셀에서 아예 단서도 못 찾은 경우
                details.append({
                    "input_name": item["input_name"],
                    "status": "not_found",
                    "quantity": item["quantity"],
                    "unit": item["unit"]
                })
            else:
                candidates = []
                # 용의자 5명 전부의 영양소를 섭취량(비율)에 맞게 꼼꼼히 계산합니다.
                for row in db_results:
                    ratio = item["quantity"]
                    
                    calories = round(row["에너지(kcal)"] * ratio, 1)
                    protein = round(row["단백질(g)"] * ratio, 1)
                    fat = round(row["지방(g)"] * ratio, 1)
                    carbs = round(row["탄수화물(g)"] * ratio, 1)
                    
                    candidates.append({
                        "식품명": row["식품명"],
                        "기준량": f"{row['1회제공량(g)']}g",
                        "nutrition": {
                            "칼로리": calories,
                            "단백질": protein,
                            "지방": fat,
                            "탄수화물": carbs
                        }
                    })

                details.append({
                    "input_name": item["input_name"],
                    "status": "candidates_found",
                    "quantity": item["quantity"],
                    "unit": item["unit"],
                    "candidates": candidates
                })

        return {
            "status": "success",
            "total_nutrition": total_nutrition,
            "details": details
        }
