import pandas as pd
from config import Config

class FoodDBManager:
    def __init__(self, db_path: str = None):
        # Config에서 절대 경로를 가져와 사용
        self.db_path = db_path or Config.FOOD_DB_PATH
        self.df = None
        self._load_db()

    def _load_db(self):
        try:
            self.df = pd.read_excel(self.db_path)
            # '식품명' 컬럼이 있으면 양쪽 공백 제거
            if "식품명" in self.df.columns:
                self.df["식품명"] = self.df["식품명"].astype(str).str.strip()
        except Exception as e:
            print(f"🚨 DB 파일 로딩 실패: {e}")
            self.df = pd.DataFrame() 

    def search_by_name(self, search_keywords: list[str]) -> list[dict]:
        """
        NLU가 만들어준 다중 키워드 리스트를 받아서 순서대로 검색합니다.
        (예: ['멥쌀밥', '쌀밥', '밥'])
        """
        if self.df.empty:
            return []

        matched_df = pd.DataFrame()
        
        # 1. 키워드 순서대로 (정밀 -> 포괄) 그물망 검색 시도
        for keyword in search_keywords:
            keyword = keyword.strip()
            if not keyword:
                continue
            
            # 띄어쓰기가 있다면 교집합(AND) 검색 (예: '구운 치킨' -> '구운' AND '치킨')
            if " " in keyword:
                words = keyword.split()
                mask = self.df["식품명"].str.contains(words[0], case=False, na=False)
                for w in words[1:]:
                    mask = mask & self.df["식품명"].str.contains(w, case=False, na=False)
                temp_df = self.df[mask]
            else:
                # 단일 단어 검색
                mask = self.df["식품명"].str.contains(keyword, case=False, na=False)
                temp_df = self.df[mask]

            # 2. 결과가 하나라도 나오면 더 포괄적인 단어로는 찾지 않고 스톱!
            if not temp_df.empty:
                matched_df = temp_df
                break

        # 3. 매칭된 데이터가 있다면 이름이 가장 짧은 것(기본 음식)이 위로 오도록 정렬
        if not matched_df.empty:
            matched_df = matched_df.assign(name_len=matched_df["식품명"].str.len())
            matched_df = matched_df.sort_values(by="name_len")

        results = []
        # 상위 5개 정도만 뽑아서 리스트로 변환
        for _, row in matched_df.head(5).iterrows():
            results.append({
                "식품명": row.get("식품명", "미상"),
                "에너지(kcal)": float(row.get("에너지(kcal)", 0) if pd.notna(row.get("에너지(kcal)")) else 0),
                "단백질(g)": float(row.get("단백질(g)", 0) if pd.notna(row.get("단백질(g)")) else 0),
                "지방(g)": float(row.get("지방(g)", 0) if pd.notna(row.get("지방(g)")) else 0),
                "탄수화물(g)": float(row.get("탄수화물(g)", 0) if pd.notna(row.get("탄수화물(g)")) else 0),
                "1회제공량(g)": float(row.get("1회제공량(g)", 100) if pd.notna(row.get("1회제공량(g)")) else 100)
            })

        return results
