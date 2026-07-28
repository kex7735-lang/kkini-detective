import streamlit as st
import uuid
import time
import re
import base64
from langchain_core.messages import HumanMessage
from graph_agent import nutrition_agent_app

AI_AVATAR = "detective.png"

# 💡 [핵심 수정 1] 브라우저 탭 아이콘(page_icon)에서도 이모지를 빼고 커스텀 이미지 변수로 대체!
# 주의: st.set_page_config는 변수 선언보다 아래에 있어야 하므로 위치를 살짝 내렸습니다.
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
        progress = min(st.session_state.daily_kcal / st.session_state.target_kcal, 1.0) if st.session_state.target_kcal > 0 else 0
        
        if progress < 0.8:
            st.progress(progress)
            st.success(f"✅ 누적 섭취량: **{st.session_state.daily_kcal}** / {st.session_state.target_kcal} kcal (여유)")
        elif progress <= 1.0:
            st.progress(progress)
            st.warning(f"⚠️ 누적 섭취량: **{st.session_state.daily_kcal}** / {st.session_state.target_kcal} kcal (주의)")
        else:
            st.progress(1.0)
            st.error(f"🚨 누적 섭취량: **{st.session_state.daily_kcal}** / {st.session_state.target_kcal} kcal (초과!)")

    st.divider()
    if st.button("🔄 새로운 대화 (초기화)"):
        st.session_state.messages = []
        st.session_state.daily_kcal = 0.0
        st.session_state.thread_id = str(uuid.uuid4())
        st.rerun()

# 3. 메인 화면
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
        
        # 💡 [핵심 수정 2] 로딩 텍스트 안에 남아있던 이모지도 완벽하게 제거!
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
        
        context_prompt = f"[시스템 메모: 당신은 '끼니탐정'입니다. 내 이름은 {st.session_state.user_name}이고, 오늘 하루 권장 칼로리는 {st.session_state.target_kcal}kcal야. 그리고 방금 전까지 나의 누적 섭취량은 {st.session_state.daily_kcal}kcal였어. 계산기를 돌린 후, 기존 누적량에 방금 먹은 칼로리를 더해서 수사 결과를 숫자로 명확히 브리핑해줘.]\n\n나의 말: {prompt}"
        
        inputs = {"messages": [HumanMessage(content=context_prompt)]}
        final_response = ""
        is_tool_used = False
        
        for event in nutrition_agent_app.stream(inputs, config=config, stream_mode="updates"):
            if "chatbot" in event:
                final_response = event["chatbot"]["messages"][0].content
            elif "tools" in event:
                is_tool_used = True
                tool_msg = str(event["tools"]["messages"][0].content)
                match = re.search(r"총 칼로리:\s*([0-9.,]+)", tool_msg)
                if match:
                    val = float(match.group(1).replace(",", ""))
                    st.session_state.daily_kcal += val
                    st.session_state.daily_kcal = round(st.session_state.daily_kcal, 1)

        loading_overlay.empty()
        st.markdown(final_response)
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        
        if is_tool_used:
            time.sleep(0.5)
            st.rerun()