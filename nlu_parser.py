from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from config import Config

class FoodItem(BaseModel):
    input_name: str = Field(
        description="사용자가 말한 원본 음식 이름 (예: 공기밥, 뿌링클 치킨, 마라탕)"
    )
    search_keywords: list[str] = Field(
        description="DB 검색을 위한 키워드 목록. 1순위: 정식 명칭, 2순위: 핵심 명사, 3순위: 포괄적 단어 (예: ['멥쌀밥', '쌀밥', '밥'])"
    )
    quantity: float = Field(
        description="수량. '반', '조금' 등은 0.5로 변환. 언급 없으면 1.0", 
        default=1.0
    )
    unit: str = Field(
        description="단위. (예: 인분, 개, 공기, 마리 등)", 
        default="인분"
    )

class MealExtraction(BaseModel):
    items: list[FoodItem] = Field(description="추출된 음식 목록")

class NaturalLanguageParser:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o", 
            temperature=0, 
            openai_api_key=Config.OPENAI_API_KEY
        )
        self.structured_llm = self.llm.with_structured_output(MealExtraction)

    def parse_meal(self, text: str) -> dict:
        try:
            prompt = (
                "당신은 천재적인 음식 데이터 분석기입니다. 사용자의 식사 기록에서 음식을 추출하고, "
                "DB 검색을 위한 그물망 키워드 후보를 만드세요.\n"
                "1. input_name: 사용자가 말한 그대로의 이름\n"
                "2. search_keywords: 엑셀 DB에서 찾을 수 있도록 구체적인 정식 명칭부터 "
                "포괄적 단어까지 3~4개 정도의 리스트를 작성하세요.\n"
                "   (예: '치킨 반마리랑 공기밥 반개' -> 치킨은 ['프라이드치킨', '치킨'], 밥은 ['멥쌀밥', '쌀밥', '밥'])\n"
                f"문장: {text}"
            )
            result = self.structured_llm.invoke(prompt)
            
            items = []
            for item in result.items:
                items.append({
                    "input_name": item.input_name,
                    "search_keywords": item.search_keywords,
                    "quantity": item.quantity,
                    "unit": item.unit
                })
            return {"items": items}
            
        except Exception as e:
            print(f"🚨 파싱 에러: {e}")
            return {"items": []}
