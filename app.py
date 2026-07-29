import streamlit as st
import uuid
import time
import re
import base64
from langchain_core.messages import HumanMessage
from graph_agent import nutrition_agent_app

AI_AVATAR = "detective.png"

# 💡 브라우저 탭 아이콘(page_icon) 커스텀 이미지 변수로 대체
st.set_page_config(page_title="끼니탐정", page_icon=AI_AVATAR, layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Jua&display=swap');
    
    .title-font {
        font-family: 'Jua', sans-serif;
        font-size: 3.5rem;
        color: #2C3E50;
        margin: 0;
        padding-top: 15px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def get_base64_image(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

try:
    detective_b64 = get_base64_image(AI_AVATAR)
except:
    detective_b64 = ""

if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "daily_kcal" not in st.session_state:
    st.session_state.daily_kcal = 0.0

if "total_protein" not in st.session_state:
    st.session_state.total_protein = 0.0
if "total_fat" not in st.session_state:
    st.session_state.total_fat = 0.0
if "total_carbs" not in st.session_state:
    st.session_state.total_carbs = 0.0

if "profile_set" not in st.session_state:
    st.session_state.profile_set = False
if "show_settings" not in st.session_state:
    st.session_state.show_settings = True  
    
if "user_name" not in st.session_state: st.session_state.user_name = "사용자"
if "gender" not in st.session_state: st.session_state.gender = "남성"
if "age" not in st.session_state: st.session_state.age = 30
if "height" not in st.session_state: st.session_state.height = 170.0
if "weight" not in st.session_state: st.session_state.weight = 65.0
if "target_kcal" not in st.session_state: st.session_state.target_kcal = 2000.0

with st.sidebar:
    if not st.session_state.profile_set or st.session_state.show_settings:
        st.title("⚙️ 내 프로필 설정")
        name = st.text_input("이름", value=st.session_state.user_name)
        
        gender_index = 0 if st.session_state.gender == "남성" else 1
        gender = st.selectbox("성별", ["남성", "여성"], index=gender_index)
        
        age = st.number_input("나이 (만)", min_value=10, max_value=100, value=st.session_state.age)
        height = st.number_input("키 (cm)", min_value=100.0, max_value=250.0, value=st.session_state.height, step=1.0)
        weight = st.number_input("몸무게 (kg)", min_value=30.0, max_value=200.0, value=st.session_state.weight, step=1.0)
        
        if st.button("프로필 저장 및 닫기", type="primary"):
            st.session_state.user_name = name
            st.session_state.gender = gender
            st.session_state.age = age
            st.session_state.height = height
            st.session_state.weight = weight
            
            if gender == "남성":
                bmr = (10 * weight) + (6.25 * height) - (5 * age) + 5
            else:
                bmr = (10 * weight) + (6.25 * height) - (5 * age) - 161
                
            st.session_state.target_kcal = round(bmr * 1.2)
            st.session_state.profile_set = True
            st.session_state.show_settings = False 
            st.rerun()
    else:
        if st.button("⚙️ 개인정보 수정하기"):
            st.session_state.show_settings = True
            st.rerun()

    if st.session_state.profile_set:
        st.divider()
        st.title("📊 오늘의 영양 현황")
        
        current_cal = st.session_state.daily_kcal
        goal_cal = st.session_state.target_kcal
        
        st.write(f"**누적 칼로리:** {current_cal:,.1f} / {goal_cal:,.1f} kcal")
        
        if current_cal <= goal_cal:
            percentage = min((current_cal / goal_cal) * 100, 100)
            st.markdown(f"""
            <div style="background-color: #e6e6e6; border-radius: 10px; width: 100%; height: 25px; margin-bottom: 20px;">
                <div style="background-color: #4CAF50; width: {percentage}%; height: 25px; border-radius: 10px; transition: 0.5s;"></div>
            </div>
            """, unsafe_allow_html=True)
            if percentage < 80:
                st.success("여유 있습니다! 😋")
            else:
                st.warning("주의! 권장량에 가까워집니다. ⚠️")
        else:
            st.markdown(f"""
            <div style="background-color: #e6e6e6; border-radius: 10px; width: 100%; height: 25px; margin-bottom: 5px;">
                <div style="background-color: #4CAF50; width: 100%; height: 25px; border-radius: 10px;"></div>
            </div>
            """, unsafe_allow_html=True)
            
            over_percentage = min(((current_cal - goal_cal) / goal_cal) * 100, 100)
            st.markdown(f"""
            <div style="background-color: #e6e6e6; border-radius: 10px; width: 100%; height: 25px; margin-bottom: 5px;">
                <div style="background-color: #F44336; width: {over_percentage}%; height: 25px; border-radius: 10px; transition: 0.5s;"></div>
            </div>
            """, unsafe_allow_html=True)
            st.error(f"🚨 권장량을 {current_cal - goal_cal:,.1f} kcal 초과했습니다!")

        st.markdown(f"""
        <div style="display: flex; justify-content: space-around; text-align: center; font-size: 0.9rem; background-color: #f0f2f6; padding: 15px 5px; border-radius: 10px; margin-top: 10px;">
            <div>
                <span style="font-size: 1.3rem;">🍚</span><br>
                <span style="color: #555; font-weight: bold; font-size: 0.85rem;">탄수화물</span><br>
                <span style="font-size: 1.1rem; color: #2C3E50; font-weight: 900;">{st.session_state.total_carbs:,.1f}g</span>
            </div>
            <div>
                <span style="font-size: 1.3rem;">🥩</span><br>
                <span style="color: #555; font-weight: bold; font-size: 0.85rem;">단백질</span><br>
                <span style="font-size: 1.1rem; color: #2C3E50; font-weight: 900;">{st.session_state.total_protein:,.1f}g</span>
            </div>
            <div>
                <span style="font-size: 1.3rem;">🧈</span><br>
                <span style="color: #555; font-weight: bold; font-size: 0.85rem;">지방</span><br>
                <span style="font-size: 1.1rem; color: #2C3E50; font-weight: 900;">{st.session_state.total_fat:,.1f}g</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    if st.button("🔄 새로운 대화 (초기화)"):
        st.session_state.messages = []
        st.session_state.daily_kcal = 0.0
        st.session_state.total_protein = 0.0
        st.session_state.total_fat = 0.0
        st.session_state.total_carbs = 0.0
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

col_img, col_txt = st.columns([1, 4], vertical_alignment="center")
with col_img:
    st.image(AI_AVATAR, width=120)
with col_txt:
    st.markdown('<h1 class="title-font">끼니탐정</h1>', unsafe_allow_html=True)

if st.session_state.profile_set:
    st.info(f"🎯 **{st.session_state.user_name}**님의 하루 권장 칼로리는 **{st.session_state.target_kcal} kcal** 입니다.")
else:
    st.caption("👈 왼쪽 사이드바에서 프로필을 설정하면 끼니탐정의 맞춤형 수사가 시작됩니다.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else AI_AVATAR):
        st.markdown(msg["content"])

if prompt := st.chat_input("사건 단서(식사 기록)를 입력해 주세요 (예: 치킨 반 마리 먹었어)"):
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=AI_AVATAR):
        loading_overlay = st.empty()
        
        loading_overlay.markdown(f"""
            <style>
            .loading-screen {{
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0, 0, 0, 0.85); backdrop-filter: blur(5px); 
                z-index: 99999; display: flex; flex-direction: column;
                align-items: center; justify-content: center;
            }}
            .detective-img {{
                width: 220px; 
                border-radius: 50%;
                margin-bottom: 25px;
                box-shadow: 0 0 30px rgba(255, 215, 0, 0.4);
                animation: float 2s ease-in-out infinite;
            }}
            @keyframes float {{
                0% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-15px); }}
                100% {{ transform: translateY(0px); }}
            }}
            .loading-text {{ color: white; font-size: 1.3rem; font-weight: 500; margin-top: 10px; }}
            </style>
            <div class="loading-screen">
                <img src="data:image/png;base64,{detective_b64}" class="detective-img">
                <div class="loading-text">끼니탐정이 사건 단서를 분석하고 있습니다...</div>
            </div>
        """, unsafe_allow_html=True)

        config = {"configurable": {"thread_id": st.session_state.thread_id}}
        
        # 💡 [핵심 수정] "식단 짜줘" 등에는 0kcal로 뱉어내서 앱 게이지를 건드리지 않게 지시
        hidden_instruction = (
            f"[시스템 메모: 당신은 '끼니탐정'입니다. 내 이름은 {st.session_state.user_name}이고, 오늘 하루 권장 칼로리는 {st.session_state.target_kcal}kcal야. "
            f"그리고 방금 전까지 나의 누적 섭취량은 {st.session_state.daily_kcal}kcal였어.]\n\n"
            f"나의 말: {prompt}\n\n"
            "(시스템 중요 지시사항: 만약 사용자가 '실제로 먹은 음식'을 기록한 거라면 맨 마지막 줄에 반드시 `[이번 식사: 000kcal, 단백질: 00g, 지방: 00g, 탄수화물: 00g]` 양식으로 '방금 먹은 수치만' 출력하세요.\n"
            "🚨주의: 하지만 만약 사용자가 '식단을 짜달라'고 하거나, 아직 먹지 않은 음식에 대해 '질문'한 거라면 미래형/설명형으로 추천만 해주고, 누적 게이지가 오르지 않도록 맨 마지막 줄에 무조건 `[이번 식사: 0kcal, 단백질: 0g, 지방: 0g, 탄수화물: 0g]` 이라고 적으세요!)"
        )
        
        inputs = {"messages": [HumanMessage(content=hidden_instruction)]}
        final_response = ""
        is_tool_used = False
        
        for event in nutrition_agent_app.stream(inputs, config=config, stream_mode="updates"):
            if "chatbot" in event:
                final_response = event["chatbot"]["messages"][0].content
            elif "tools" in event:
                is_tool_used = True

        match = re.search(r'\[이번 식사:\s*([0-9,.]+)\s*kcal,\s*단백질:\s*([0-9,.]+)\s*g,\s*지방:\s*([0-9,.]+)\s*g,\s*탄수화물:\s*([0-9,.]+)\s*g\]', final_response)
        
        if match:
            st.session_state.daily_kcal += float(match.group(1).replace(',', ''))
            st.session_state.total_protein += float(match.group(2).replace(',', ''))
            st.session_state.total_fat += float(match.group(3).replace(',', ''))
            st.session_state.total_carbs += float(match.group(4).replace(',', ''))
            
            st.session_state.daily_kcal = round(st.session_state.daily_kcal, 1)
            st.session_state.total_protein = round(st.session_state.total_protein, 1)
            st.session_state.total_fat = round(st.session_state.total_fat, 1)
            st.session_state.total_carbs = round(st.session_state.total_carbs, 1)

        clean_response = re.sub(r'\[이번 식사:.*?\]', '', final_response).strip()

        loading_overlay.empty()
        st.markdown(clean_response)
        st.session_state.messages.append({"role": "assistant", "content": clean_response})
        
        if is_tool_used:
            time.sleep(0.5)
            st.rerun()
