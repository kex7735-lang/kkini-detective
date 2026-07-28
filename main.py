from graph_agent import nutrition_agent_app
from langchain_core.messages import HumanMessage

def run_chat():
    print("\n=========================================================")
    print(" 🥗 AI 영양사 챗봇이 시작되었습니다! (종료하려면 '종료' 입력) ")
    print("=========================================================\n")
    
    # 💡 [핵심] 대화방 ID 설정 (이 ID를 기준으로 대화를 기억합니다)
    config = {"configurable": {"thread_id": "user_1"}}
    
    while True:
        user_input = input("👤 당신: ")
        
        if user_input.strip() in ['quit', 'exit', '종료', '그만']:
            print("\n👋 AI 영양사: 식단 관리가 필요할 때 언제든 다시 찾아주세요! 건강한 하루 보내세요!")
            break
            
        if not user_input.strip():
            continue

        inputs = {"messages": [HumanMessage(content=user_input)]}
        
        # 💡 [수정] 실행 시 config(thread_id)를 함께 넘겨줍니다.
        for event in nutrition_agent_app.stream(inputs, config=config, stream_mode="values"):
            message = event["messages"][-1]
            
            if message.type == "ai" and not message.tool_calls:
                print(f"\n👩‍⚕️ AI 영양사: {message.content}\n")

if __name__ == "__main__":
    run_chat()