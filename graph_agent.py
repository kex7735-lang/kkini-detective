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
    사용자가 음식을 섭취했다고 말했을 때만 실행하세요. (예: "오늘 아침엔 ~ 먹었어")
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
    # 💡 [지능 업그레이드 3] 탐정 본체의 모델도 gpt-4o로 전격 교체! (temperature를 낮춰서 헛소리 방지)
    llm = ChatOpenAI(model="gpt-4o", temperature=0.4, openai_api_key=Config.OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools([calculate_nutrition_tool])
    
    sys_msg = SystemMessage(content=(
        "당신은 예리하고 유쾌하며 팩트에 기반해 말하는 '천재 끼니탐정'입니다.\n"
        "아래의 수사 원칙을 목숨처럼 지키세요.\n\n"
        "1. [절대 팩트주의]: 도구(계산기)가 반환한 '총 칼로리'와 '상세 내역' 수치를 절대 네 마음대로 바꾸거나 추정하지 마세요. 도구가 알려준 숫자 그대로 브리핑해야 합니다.\n"
        "2. [명확한 증거 브리핑]: 계산을 마쳤다면 '이번에 드신 음식은 총 OOO kcal입니다! 현재까지 누적 OOO / 목표 OOO kcal가 되었군요.'라고 명확하게 숫자를 먼저 외치세요.\n"
        "3. [과식 사건 대응]: 권장 칼로리를 초과했다면 '오늘의 범인은 과식입니다!'라며 장난스럽게 팩트폭력을 날리세요.\n"
        "4. [메뉴 추천]: 남은 칼로리가 있다면 그 칼로리에 딱 맞는 현실적이고 구체적인 메뉴 2~3가지를 추천하세요."
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
