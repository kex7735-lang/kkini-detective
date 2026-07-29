import streamlit as st
import re
import uuid
from graph_agent import nutrition_agent_app

# ---------------------------------------------------------
# 1. 페이지 설정 및 초기화
# ---------------------------------------------------------
st.set_page_config(page_title="천재 끼니탐정", page_icon="🕵️‍♂️", layout="centered")

# 대화 기록 및 영양소 누적 상태 저장
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())

# 4대 영양소 세션 상태 초기화
if "total_calories" not in st.session_state:
    st.session_state.total_calories = 0.0
if "total_protein" not in st.session_state:
    st.session_state.total_protein = 0.0
if "total_fat" not in st.session_state:
    st.session_state.total_fat = 0.0
if "total_carbs" not in st.session_state:
    st.session_state.total_carbs = 0.0

# ---------------------------------------------------------
# 2. UI 대시보드 렌더링 (칼로리 듀얼 바 & 탄단지)
# ---------------------------------------------------------
st.title("🕵️‍♂️ 천재 끼니탐정")
st.caption("먹은 음식을 말해주시면, 숨겨진 칼로리와 영양소를 끝까지 추적해 냅니다!")

GOAL_CALORIES = 2000.0  # 하루 권장 목표 칼로리
current_cal = st.session_state.total_calories

st.write("---")
st.write(f"📊 **오늘의 누적 칼로리:** {current_cal:,.1f} / {GOAL_CALORIES:,.1f} kcal")

# [핵심] 칼로리 초과 시 빨간색 게이지가 새로 차오르는 커스텀 UI
if current_cal <= GOAL_CALORIES:
    percentage = min((current_cal / GOAL_CALORIES) * 100, 100)
    st.markdown(f"""
    <div style="background-color: #e6e6e6; border-radius: 10px; width: 100%; height: 25px; margin-bottom: 20px;">
        <div style="background-color: #4CAF50; width: {percentage}%; height: 25px; border-radius: 10px; transition: 0.5s;"></div>
    </div>
    """, unsafe_allow_html=True)
else:
    # 1. 100% 꽉 찬 초록색 기본 바
    st.markdown(f"""
    <div style="background-color: #e6e6e6; border-radius: 10px; width: 100%; height: 25px; margin-bottom: 5px;">
        <div style="background-color: #4CAF50; width: 100%; height: 25px; border-radius: 10px;"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # 2. 초과분을 나타내는 빨간색 듀얼 바
    over_percentage = min(((current_cal - GOAL_CALORIES) / GOAL_CALORIES) * 100, 100)
    st.markdown(f"""
    <div style="background-color: #e6e6e6; border-radius: 10px; width: 100%; height: 25px; margin-bottom: 5px;">
        <div style="background-color: #F44336; width: {over_percentage}%; height: 25px; border-radius: 10px; transition: 0.5s;"></div>
    </div>
    <p style="color: #F44336; font-size: 14px; font-weight: bold; margin-bottom: 20px;">
        ⚠️ 권장 칼로리를 {current_cal - GOAL_CALORIES:,.1f} kcal 초과했습니다! 과식 탐정 출동 대기 중! 🚨
    </p>
    """, unsafe_allow_html=True)

# 3대 영양소 표시 (탄수화물, 지방, 단백질)
col1, col2, col3 = st.columns(3)
col1.metric("🍚 탄수화물", f"{st.session_state.total_carbs:,.1f} g")
col2.metric("🥩 단백질", f"{st.session_state.total_protein:,.1f} g")
col3.metric("🧈 지방", f"{st.session_state.total_fat:,.1f} g")
st.write("---")

# ---------------------------------------------------------
# 3. 채팅 UI 및 에이전트 연동
# ---------------------------------------------------------
# 기존 대화 기록 출력
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# 사용자 입력 처리
if prompt = st.chat_input("오늘 어떤 음식을 드셨나요? (예: 치킨 반마리에 콜라 한 잔 먹었어)"):
    # 화면에 사용자 메시지 표시
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("수첩을 뒤적이며 단서를 찾는 중..."):
            
            # [핵심] 탐정이 영양소를 정확히 뱉어내도록 시스템 몰래 지령을 추가합니다.
            hidden_instruction = (
                f"{prompt}\n\n"
                "(시스템 지시사항: 브리핑 맨 마지막 줄에 반드시 아래 양식을 토씨 하나 틀리지 말고 출력하세요. "
                "이 값은 누적값이 아니라 '방금 먹은 음식만의' 영양소 합이어야 합니다.\n"
                "양식: [이번 식사: 000kcal, 단백질: 00g, 지방: 00g, 탄수화물: 00g])"
            )

            # 탐정(LangGraph)에게 수사 의뢰
            config = {"configurable": {"thread_id": st.session_state.thread_id}}
            result = nutrition_agent_app.invoke({"messages": [("user", hidden_instruction)]}, config)
            
            # 탐정의 전체 대답 가져오기
            raw_response = result["messages"][-1].content
            
            # ---------------------------------------------------------
            # 4. 정규식을 통한 영양소 추출 및 깔끔한 화면 출력
            # ---------------------------------------------------------
            # 숨겨놓은 '[이번 식사: ...]' 포맷을 찾아서 숫자를 뽑아냅니다.
            match = re.search(r'\[이번 식사:\s*([0-9,.]+)\s*kcal,\s*단백질:\s*([0-9,.]+)\s*g,\s*지방:\s*([0-9,.]+)\s*g,\s*탄수화물:\s*([0-9,.]+)\s*g\]', raw_response)
            
            if match:
                # 쉼표(,)를 제거하고 숫자로 변환하여 누적
                st.session_state.total_calories += float(match.group(1).replace(',', ''))
                st.session_state.total_protein += float(match.group(2).replace(',', ''))
                st.session_state.total_fat += float(match.group(3).replace(',', ''))
                st.session_state.total_carbs += float(match.group(4).replace(',', ''))

            # 사용자 화면에 보여줄 때는 지저분한 '[이번 식사: ...]' 꼬리표를 잘라내고 렌더링합니다.
            clean_response = re.sub(r'\[이번 식사:.*?\]', '', raw_response).strip()
            
            st.markdown(clean_response)
            st.session_state.messages.append({"role": "assistant", "content": clean_response})

    # UI 갱신을 위해 화면을 즉시 새로고침 (바와 대시보드 수치 갱신)
    st.rerun()
