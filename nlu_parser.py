from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from config import Config

# 💡 [핵심] AI에게 "음식, 수량, 단위"를 어떤 양식으로 뽑아낼지 강제하는 틀(Schema)
class FoodItem(BaseModel):
    food_name: str = Field(description="음식 이름 (예: 김치볶음밥, 후라이드 치킨)")
    quantity: float = Field(description="수량. 숫자로만 표시. 언급이 없으면 1.0", default=1.0)
    unit: str = Field(description="단위 (예: 인분, 그램, 개, 마리). 언급이 없으면 '인분'", default="인분")

class MealExtraction(BaseModel):
    items: list[FoodItem] = Field(description="추출된 음식 목록")

class NaturalLanguageParser:
    def __init__(self):
        # 정보 추출에만 100% 집중하도록 창의성(temperature)을 0으로 뚝 떨어뜨림
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=Config.OPENAI_API_KEY)
        self.structured_llm = self.llm.with_structured_output(MealExtraction)

    def parse_meal(self, text: str) -> dict:
        try:
            # 💡 [핵심] 수량/단위가 없으면 '1인분'으로 알아서 채워넣으라고 강력하게 지시
            prompt = (
                "다음 문장에서 먹은 음식 이름과 수량, 단위를 추출해줘. "
                "수량이나 단위가 명시되지 않았다면 기본값으로 수량은 1, 단위는 '인분'으로 설정해.\n"
                f"문장: {text}"
            )
            result = self.structured_llm.invoke(prompt)
            
            items = []
            for item in result.items:
                items.append({
                    "food_name": item.food_name,
                    "quantity": item.quantity,
                    "unit": item.unit
                })
            return {"items": items}
            
        except Exception as e:
            print(f"🚨 파싱 에러: {e}")
            return {"items": []}