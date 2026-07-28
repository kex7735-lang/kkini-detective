import pandas as pd
import os

def process_raw_food_db():
    raw_db_path = "data/raw_food_db.xlsx"
    processed_db_path = "data/food_db.xlsx"
    
    print("\n[농촌진흥청 DB 정밀 전처리 시작 🚀]")
    
    if not os.path.exists(raw_db_path):
        print(f"🚨 오류: {raw_db_path} 파일이 없습니다.")
        return

    try:
        print("📂 엑셀 구조 분석 및 데이터 추출 중... (약 10~30초 소요)")
        xls = pd.ExcelFile(raw_db_path)
        
        # 진짜 데이터가 들어있는 시트들만 필터링합니다. (버전에 따라 10.0~10.4 등 다양함)
        target_sheets = [sheet for sheet in xls.sheet_names if sheet.startswith("국가표준식품성분 Database")]
        
        if not target_sheets:
            print("🚨 '국가표준식품성분 Database'로 시작하는 시트를 찾을 수 없습니다.")
            return

        all_data = []
        
        # 각 시트를 순회하며 데이터를 추출합니다.
        for sheet in target_sheets:
            print(f"   -> 📑 '{sheet}' 시트 처리 중...")
            # 농진청 엑셀은 1번째 줄(0번 인덱스)에 병합된 제목이 있고, 2번째 줄(1번 인덱스)에 진짜 헤더가 있습니다.
            # header=1 옵션으로 2번째 줄을 진짜 컬럼명으로 인식하게 합니다.
            df = pd.read_excel(raw_db_path, sheet_name=sheet, header=1)
            
            # '식품명' 컬럼이 있는 데이터만 취합 (빈 줄이나 설명 줄 제거)
            if '식품명' in df.columns:
                # 우리가 필요한 5개의 핵심 컬럼만 추출 ('지방'은 원본 엑셀에 공백이 포함된 '지방 '일 수 있으므로 유연하게 처리)
                # 컬럼명에 앞뒤 공백이 있을 수 있으니 미리 싹 지워줍니다.
                df.columns = df.columns.str.strip() 
                
                # 추출할 컬럼 목록 (만약 없는 영양소가 있다면 0으로 채움)
                core_cols = ['식품명', '에너지', '탄수화물', '단백질', '지방']
                
                # 현재 시트에서 추출할 수 있는 컬럼만 골라냅니다.
                available_cols = [col for col in core_cols if col in df.columns]
                extracted_df = df[available_cols].copy()
                
                # 누락된 영양소 컬럼이 있다면 0으로 생성
                for col in core_cols:
                    if col not in extracted_df.columns:
                        extracted_df[col] = 0
                
                all_data.append(extracted_df)

        if not all_data:
            print("🚨 데이터를 하나도 추출하지 못했습니다.")
            return

        print("\n🔍 데이터 취합 및 최종 정제 중...")
        # 모든 시트의 데이터를 하나의 거대한 데이터프레임으로 합칩니다.
        final_df = pd.concat(all_data, ignore_index=True)
        
        # '식품명'이 비어있는 쓸모없는 행(Row) 완벽 제거
        final_df = final_df.dropna(subset=['식품명'])
        
        # 이름 앞뒤 공백 제거
        final_df['식품명'] = final_df['식품명'].astype(str).str.strip()
        
        # '에너지', '탄수화물', '단백질', '지방' 컬럼을 숫자형으로 변환 (글자가 섞여있으면 강제로 NaN 처리 후 0으로 변환)
        for col in ['에너지', '탄수화물', '단백질', '지방']:
            final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)

        # -------------------------------------------------------------
        # ★ 우리 에이전트 표준 규격(db_manager.py)에 맞춰 컬럼 이름 변경
        # -------------------------------------------------------------
        final_df = final_df.rename(columns={
            '에너지': '에너지(kcal)',
            '탄수화물': '탄수화물(g)',
            '단백질': '단백질(g)',
            '지방': '지방(g)'
        })
        
        # 농진청 원본 DB는 모두 100g 당 영양소 기준이므로, '1회제공량(g)'을 일괄 100으로 설정해 줍니다.
        final_df['1회제공량(g)'] = 100.0

        # 중복된 음식 이름이 있다면 첫 번째 것만 남기고 제거 (검색 엔진 꼬임 방지)
        final_df = final_df.drop_duplicates(subset=['식품명'], keep='first')

        print(f"💾 정제된 DB 저장 중... (총 {len(final_df)}개 식품 항목)")
        # 엑셀 파일로 저장
        final_df.to_excel(processed_db_path, index=False)
        
        print("\n🎉 [DB 전처리 완료] 엑셀 데이터가 완벽하게 다듬어졌습니다!")
        print(f"-> 저장 경로: {processed_db_path}")
        print("-> 이제 python main.py를 실행하여 실제 데이터로 검색되는지 테스트해 보세요.")
        
    except Exception as e:
         print(f"🚨 처리 중 오류 발생: {e}")

if __name__ == "__main__":
    process_raw_food_db()