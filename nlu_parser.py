from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from config import Config

class FoodItem(BaseModel):
    # 💡 [핵심] 일상어를 공공 DB 표준어로 알아서 번역하라고 강력하게 지시!
    food_name: str = Field(description="음식 이름. 단, 검색이 잘 되도록 정식 명칭으로 정제하세요. (예: '공기밥'->'멥쌀밥', '치킨'->'프라이드치킨', '계란'->'달걀')")
    quantity: float = Field(description="수량. '반 마리', '반 개'는 0.5로 변환. 언급이 없으면 기본값 1.0", default=1.0)
    unit: str = Field(description="단위. (예: 인분, 그램, 개, 마리, 그릇 등)", default="인분")

class MealExtraction(BaseModel):
    items: list[FoodItem] = Field(description="추출된 음식 목록")

class NaturalLanguageParser:
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0, openai_api_key=Config.OPENAI_API_KEY)
        self.structured_llm = self.llm.with_structured_output(MealExtraction)

    def parse_meal(self, text: str) -> dict:
        try:
            prompt = (
                "당신은 천재적인 음식 데이터 추출기입니다. 사용자의 식사 기록에서 음식 이름, 수량, 단위를 정확히 추출하세요.\n"
                "- 반드시 공공 영양 DB(식약처)에 있을 법한 정식 표준 명칭으로 음식 이름을 정제하세요.\n"
                "- 예: '치킨 반마리랑 공기밥 반개' -> 프라이드치킨(0.5, 마리), 멥쌀밥(0.5, 개)\n"
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
