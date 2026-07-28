import pandas as pd
import os

# data 폴더가 없으면 생성
os.makedirs("data", exist_ok=True)

# 테스트용 가짜 데이터 (실제 농촌진흥청 DB와 유사한 컬럼명 사용)
data = {
    "식품명": ["제육볶음", "쌀밥", "된장찌개", "계란후라이"],
    "에너지(kcal)": [250, 150, 80, 90],
    "단백질(g)": [15.2, 3.0, 5.5, 6.5],
    "지방(g)": [12.0, 0.5, 2.0, 7.0],
    "탄수화물(g)": [10.5, 33.0, 8.0, 0.5],
    "1회제공량(g)": [100, 100, 100, 100]
}

df = pd.DataFrame(data)
df.to_excel("data/food_db.xlsx", index=False)
print("✅ data/food_db.xlsx 샘플 파일 생성 완료!")