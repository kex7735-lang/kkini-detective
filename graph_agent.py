from typing import Annotated, TypedDict
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver 

from nutrition_calculator import NutritionCalculator
from config import Config

calculator = NutritionCalculator()

@tool
def calculate_nutrition_tool(meal_record: str) -> str:
    """
    [경고: 엄격한 사용 조건]
    사용자가 "무엇을 얼만큼 먹었다"라고 명확히 말했을 때만(단서를 제공했을 때만) 실행하세요.
    사용자가 단순히 식단을 추천해달라고 하거나 질문할 때는 절대 실행하지 마세요.
    """
    result = calculator.process_meal_record(meal_record)
    
    if result["status"] == "error":
        return f"계산 에러 발생: {result.get('message')}"
        
    total = result["total_nutrition"]
    details_str = []
    for item in result["details"]:
        if item.get("status") == "not_found":
            details_str.append(f"- {item['food_name']} (DB 검색 실패)")
        else:
            details_str.append(f"- {item['input_name']} -> 매칭: {item['food_name']} ({item['섭취량']}): {item['nutrition']['칼로리']}kcal")
            
    details_joined = "\n".join(details_str)
    return (
        f"[시스템 계산 결과]\n"
        f"총 칼로리: {total['칼로리']}kcal (탄수화물: {total['탄수화물']}g, 단백질: {total['단백질']}g, 지방: {total['지방']}g)\n"
        f"상세 내역:\n{details_joined}"
    )

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7, openai_api_key=Config.OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools([calculate_nutrition_tool])
    
    # 💡 [핵심 수정] 무조건 "숫자(칼로리)"를 명확히 브리핑하라는 룰 추가
    sys_msg = SystemMessage(content=(
        "당신은 예리하고 유쾌한 '끼니탐정'입니다.\n"
        "아래의 수사 원칙을 반드시 지켜서 탐정 컨셉에 맞게 대화하세요.\n\n"
        "1. [명확한 증거(숫자) 브리핑]: 계산기(도구)를 사용했다면, 뭉뚱그려 말하지 말고 '방금 섭취한 음식의 정확한 칼로리', '현재까지의 총 누적 칼로리', '남은 권장 칼로리'를 명확한 숫자로 먼저 브리핑하세요! (예: '이번에 드신 치킨은 800kcal입니다! 기존 누적량과 합쳐 총 1500/2000kcal가 되었군요.')\n"
        "2. [과식 사건 대응]: 권장 칼로리를 초과하면 '오늘의 범인은 과식입니다!'라며 지적하고 '식후 30분 빠른 걸음 수사'를 처방하세요.\n"
        "3. [적극적인 식단 추천]: 식단을 추천해달라고 하면 절대 되묻지 말고, 탐정의 직감으로 남은 칼로리에 딱 맞는 구체적인 메뉴 2~3가지를 즉시 지목하세요.\n"
        "4. [문맥 유지]: 사용자의 수사 기록을 항상 기억하세요."
    ))
    
    response = llm_with_tools.invoke([sys_msg] + state["messages"])
    return {"messages": [response]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", ToolNode(tools=[calculate_nutrition_tool]))
graph_builder.add_edge(START, "chatbot")
graph_builder.add_conditional_edges("chatbot", tools_condition)
graph_builder.add_edge("tools", "chatbot")

memory = MemorySaver()
nutrition_agent_app = graph_builder.compile(checkpointer=memory)