from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from config import Config

class FoodItem(BaseModel):
    food_name: str = Field(description="음식 이름 (예: 김치볶음밥, 제육볶음, 프라이드 치킨)")
    quantity: float = Field(description="수량. 숫자로만 표시. '반 마리'는 0.5, '조금'은 0.5 등으로 문맥을 파악해 추론할 것. 언급이 없으면 1.0", default=1.0)
    unit: str = Field(description="단위 (예: 인분, 그램, 개, 마리, 공기, 그릇). 언급이 없으면 '인분'", default="인분")

class MealExtraction(BaseModel):
    items: list[FoodItem] = Field(description="추출된 음식 목록")

class NaturalLanguageParser:
    def __init__(self):
        # 💡 [지능 업그레이드 1] 3.5-turbo를 버리고 압도적인 눈치의 최신 'gpt-4o' 장착!
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=Config.OPENAI_API_KEY)
        self.structured_llm = self.llm.with_structured_output(MealExtraction)

    def parse_meal(self, text: str) -> dict:
        try:
            # 💡 [지능 업그레이드 2] AI가 모호한 표현을 어떻게 처리할지 예시를 들어 강력하게 세뇌
            prompt = (
                "당신은 천재적인 음식 데이터 추출기입니다. 사용자의 식사 기록에서 음식 이름, 수량, 단위를 정확히 추출하세요.\n"
                "- 예: '밥 한공기랑 제육볶음 조금 먹었어' -> 밥(1, 공기), 제육볶음(0.5, 인분)\n"
                "- 예: '치킨 반마리' -> 치킨(0.5, 마리)\n"
                "- 수량이나 단위가 명시되지 않았다면 한국의 일반적인 1회 섭취량을 기준으로 수량은 1, 단위는 '인분'으로 알아서 채워 넣으세요.\n"
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
