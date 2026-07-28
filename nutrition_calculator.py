# nutrition_calculator.py

from nlu_parser import NaturalLanguageParser
from db_manager import FoodDBManager

class NutritionCalculator:
    def __init__(self):
        # 귀(Parser)와 눈(DB Manager)을 초기화
        self.nlu = NaturalLanguageParser()
        self.db = FoodDBManager()

    def process_meal_record(self, text: str) -> dict:
        """
        사용자의 식사 기록을 입력받아 파싱, 검색, 계산을 총괄합니다.
        """
        # 1. NLU를 통해 문장에서 음식, 수량, 다중 검색 키워드를 추출
        extracted = self.nlu.parse_meal(text)
        
        if not extracted["items"]:
            return {"status": "error", "message": "문장에서 음식 정보를 추출하지 못했습니다."}

        total_nutrition = {"칼로리": 0, "단백질": 0, "지방": 0, "탄수화물": 0}
        details = []

        # 2. 추출된 음식별로 DB 검색 및 계산 진행
        for item in extracted["items"]:
            # NLU가 만들어준 다중 키워드 리스트(search_keywords)로 DB 검색 시도
            db_results = self.db.search_by_name(item["search_keywords"])
            
            if not db_results:
                # [핵심] 그물망 검색으로도 끝내 못 찾았으면, 에러를 내거나 0으로 치지 않고
                # 'not_found' 상태로 저장하여 탐정이 나중에 추론하도록 함.
                details.append({
                    "input_name": item["input_name"],
                    "status": "not_found",
                    "quantity": item["quantity"],
                    "unit": item["unit"]
                })
            else:
                # 검색 결과 중 가장 연관성 높은 1순위(보통 가장 이름이 짧은 기본 음식) 사용
                best_match = db_results[0]
                
                # 사용자가 입력한 수량 비율 (기본 1인분/1개/1마리 = 1.0 비율)
                ratio = item["quantity"]
                
                # 섭취량에 비례한 영양성분 계산 (반올림하여 소수점 첫째자리까지)
                calories = round(best_match["에너지(kcal)"] * ratio, 1)
                protein = round(best_match["단백질(g)"] * ratio, 1)
                fat = round(best_match["지방(g)"] * ratio, 1)
                carbs = round(best_match["탄수화물(g)"] * ratio, 1)

                # 전체 영양 총합에 더함
                total_nutrition["칼로리"] += calories
                total_nutrition["단백질"] += protein
                total_nutrition["지방"] += fat
                total_nutrition["탄수화물"] += carbs

                # 계산 완료된 상세 내역 저장
                details.append({
                    "input_name": item["input_name"],
                    "food_name": best_match["식품명"],
                    "status": "found",
                    "섭취량": f"{item['quantity']}{item['unit']}",
                    "nutrition": {
                        "칼로리": calories,
                        "단백질": protein,
                        "지방": fat,
                        "탄수화물": carbs
                    }
                })

        return {
            "status": "success",
            "total_nutrition": total_nutrition,
            "details": details
        }
