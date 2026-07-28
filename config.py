import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # 1. 현재 config.py 파일이 있는 폴더의 절대 위치를 파악
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 그 폴더 위치에 엑셀 파일 이름을 딱 붙여줌
    # 🚨 '음식데이터.xlsx' 부분을 깃허브에 올라간 실제 파일명과 똑같이(대소문자 포함) 바꿔주세요!
    FOOD_DB_PATH = os.path.join(BASE_DIR, "음식데이터.xlsx")
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
