import pandas as pd
from config import Config

class FoodDBManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.FOOD_DB_PATH
        self.df = None
        self._load_db()

    def _load_db(self):
        try:
            self.df = pd.read_excel(self.db_path)
            if "식품명" in self.df.columns:
                self.df["식품명"] = self.df["식품명"].astype(str).str.strip()
        except Exception as e:
            print(f"🚨 DB 파일 로딩 실패: {e}")
            self.df = pd.DataFrame() 

    def search_by_name(self, search_keywords: list[str]) -> list[dict]:
        if self.df.empty:
            return []

        matched_df = pd.DataFrame()
        
        # 1. 귀(NLU)가 만들어준 다중 키워드를 순서대로 엑셀에서 검색
        for keyword in search_keywords:
            keyword = keyword.strip()
            if not keyword:
                continue
            
            # 띄어쓰기가 있다면 교집합(AND) 검색
            if " " in keyword:
                words = keyword.split()
                mask = self.df["식품명"].str.contains(words[0], case=False, na=False)
                for w in words[1:]:
                    mask = mask & self.df["식품명"].str.contains(w, case=False, na=False)
                temp_df = self.df[mask]
            else:
                mask = self.df["식품명"].str.contains(keyword, case=False, na=False)
                temp_df = self.df[mask]

            # 결과가 하나라도 나오면 더 뭉뚱그린 단어로는 찾지 않고 스톱!
            if not temp_df.empty:
                matched_df = temp_df
                break

        # 2. 매칭된 데이터 중 이름이 가장 짧은 것(기본 음식) 위주로 정렬
        if not matched_df.empty:
            matched_df = matched_df.assign(name_len=matched_df["식품명"].str.len())
            matched_df = matched_df.sort_values(by="name_len")

        results = []
        # 3. [핵심] 1개만 고르지 않고 상위 5개를 리스트에 담아서 반환
        for _, row in matched_df.head(5).iterrows():
            results.append({
                "식품명": row.get("식품명", "미상"),
                "1회제공량(g)": float(row.get("1회제공량(g)", 200) if pd.notna(row.get("1회제공량(g)")) else 200),
                "에너지(kcal)": float(row.get("에너지(kcal)", 0) if pd.notna(row.get("에너지(kcal)")) else 0),
                "단백질(g)": float(row.get("단백질(g)", 0) if pd.notna(row.get("단백질(g)")) else 0),
                "지방(g)": float(row.get("지방(g)", 0) if pd.notna(row.get("지방(g)")) else 0),
                "탄수화물(g)": float(row.get("탄수화물(g)", 0) if pd.notna(row.get("탄수화물(g)")) else 0)
            })

        return results
