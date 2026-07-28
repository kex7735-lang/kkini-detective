import pandas as pd
from config import Config

class FoodDBManager:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or Config.FOOD_DB_PATH
        self.df = None
        
        # 1. 완전 일치 사전: "치킨" 쳤을 때 "치킨너겟"이 나오는 대참사 방지
        self.exact_synonyms = {
            "치킨": "프라이드치킨",
            "제육볶음": "돼지고기 볶음",
            "계란후라이": "달걀"
        }
        
        # 2. 부분 일치 사전: 외래어나 브랜드명을 공공 DB 기준으로 교정
        self.partial_synonyms = {
            "후라이드": "프라이드",
            "굽네": "구운", 
            "교촌": "간장",
            "양념치킨": "양념",
            "계란": "달걀",
            "소고기": "쇠고기",
            "제육": "돼지고기",
            "쌀밥": "멥쌀밥",
            "흰밥": "멥쌀밥"
        }
        self._load_db()

    def _load_db(self):
        try:
            self.df = pd.read_excel(self.db_path)
            if "식품명" in self.df.columns:
                self.df["식품명"] = self.df["식품명"].astype(str).str.strip()
        except Exception as e:
            print(f"🚨 DB 파일 로딩 실패: {e}")
            self.df = pd.DataFrame() 

    def search_by_name(self, food_name: str) -> list[dict]:
        if self.df.empty:
            return []

        search_keyword = food_name.strip()
        
        # 동의어 변환 1: 단어가 완전히 똑같을 때
        if search_keyword in self.exact_synonyms:
            search_keyword = self.exact_synonyms[search_keyword]
        else:
            # 동의어 변환 2: 문장 안에 포함되어 있을 때 (예: 후라이드 치킨 -> 프라이드 치킨)
            for user_word, db_word in self.partial_synonyms.items():
                if user_word in search_keyword:
                    search_keyword = search_keyword.replace(user_word, db_word)

        # 1차 검색: 원형 그대로 검색
        mask = self.df["식품명"].str.contains(search_keyword, case=False, na=False)
        matched_df = self.df[mask]

        # 2차 검색: 못 찾았다면 단어를 띄어쓰기 기준으로 쪼개서 '교집합' 검색 (예: "구운 치킨" -> "구운" AND "치킨")
        if matched_df.empty and " " in search_keyword:
            words = search_keyword.split()
            mask = self.df["식품명"].str.contains(words[0], case=False, na=False)
            for w in words[1:]:
                mask = mask & self.df["식품명"].str.contains(w, case=False, na=False)
            matched_df = self.df[mask]
            
        # 3차 검색: 그래도 없다면 문장의 맨 마지막 단어(핵심어)로만 검색
        if matched_df.empty and " " in search_keyword:
            last_word = search_keyword.split()[-1]
            mask = self.df["식품명"].str.contains(last_word, case=False, na=False)
            matched_df = self.df[mask]

        # 결과가 있다면 짧고 명확한 기본 음식이 상단에 오도록 길이순 정렬
        if not matched_df.empty:
            matched_df = matched_df.assign(name_len=matched_df["식품명"].str.len())
            matched_df = matched_df.sort_values(by="name_len")

        results = []
        for _, row in matched_df.iterrows():
            results.append({
                "식품명": row.get("식품명", "미상"),
                "에너지(kcal)": float(row.get("에너지(kcal)", 0)),
                "단백질(g)": float(row.get("단백질(g)", 0)),
                "지방(g)": float(row.get("지방(g)", 0)),
                "탄수화물(g)": float(row.get("탄수화물(g)", 0)),
                "1회제공량(g)": float(row.get("1회제공량(g)", 100))
            })

        return results