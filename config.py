import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """환경 설정 중앙 관리 (로컬 DB 방식 적용)"""
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    FOOD_DB_PATH = os.getenv("FOOD_DB_PATH", "food_db.xlsx")

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == "your_openai_api_key_here":
            print("⚠️ [경고] OPENAI_API_KEY가 설정되지 않았습니다. (자연어 처리 전까지는 무시 가능)")
        
        # DB 파일이 해당 경로에 실제로 있는지 미리 검사
        if not os.path.exists(cls.FOOD_DB_PATH):
            print(f"⚠️ [경고] DB 파일을 찾을 수 없습니다: {cls.FOOD_DB_PATH}")
            print("   -> 농촌진흥청 엑셀 파일을 다운로드하여 해당 경로에 넣어주세요.")

Config.validate()
