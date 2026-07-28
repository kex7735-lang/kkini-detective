import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

class Config:
    """환경 설정 중앙 관리 (로컬 DB 방식 적용)"""
    
    # 💡 [해결책] 현재 이 코드 파일(config.py)이 있는 절대 위치를 정확히 파악!
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # 💡 깃허브에 올라간 엑셀 파일 이름이 정확히 'food_db.xlsx'인지 꼭 확인하세요! (대소문자 구별)
    FOOD_DB_PATH = os.path.join(BASE_DIR, "food_db.xlsx")

    @classmethod
    def validate(cls):
        if not cls.OPENAI_API_KEY or cls.OPENAI_API_KEY == "your_openai_api_key_here":
            print("⚠️ [경고] OPENAI_API_KEY가 설정되지 않았습니다. (자연어 처리 전까지는 무시 가능)")
        
        # DB 파일이 해당 경로에 실제로 있는지 미리 검사
        if not os.path.exists(cls.FOOD_DB_PATH):
            print(f"🚨 [에러] DB 파일을 찾을 수 없습니다: {cls.FOOD_DB_PATH}")
            print("   -> 깃허브 최상단에 파일이 있는지, 대소문자 이름이 정확한지 확인해주세요.")

Config.validate()
