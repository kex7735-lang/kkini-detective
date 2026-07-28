# graph_agent.py

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
    사용자가 음식을 먹었다고 할 때 실행하여 칼로리를 계산하는 도구입니다.
    (예: "치킨 반마리랑 밥 먹었어")
    """
    result = calculator.process_meal_record(meal_record)
    
    if result["status"] == "error":
        return f"계산 에러 발생: {result.get('message')}"
        
    total = result["total_nutrition"]
    details_str = []
    has_missing_food = False
    
    for item in result["details"]:
        if item.get("status") == "not_found":
            has_missing_food = True
            # [핵심] DB에 없는 음식은 탐정(LLM)이 직접 추정하라고 꼬리표를 달아줌
            details_str.append(f"- {item['input_name']} (DB 검색 실패: 탐정의 자체 지식으로 칼로리를 추정하여 총합에 더하세요!)")
        else:
            details_str.append(f"- {item['input_name']} -> 매칭: {item['food_name']} ({item['섭취량']}): {item['nutrition']['칼로리']}kcal")
            
    details_joined = "\n".join(details_str)
    
    # 엑셀에서 못 찾은 음식이 있을 때 탐정에게 내리는 비밀 지령
    instruction = ""
    if has_missing_food:
        instruction = "\n\n🚨 [탐정 비밀 지령]: 엑셀 DB에 없는 음식이 있습니다! 에러 났다고 하거나 당황한 티 내지 말고, 당신의 똑똑한 자체 지식을 발휘해 해당 음식의 칼로리를 합리적으로 추리한 뒤 전체 칼로리에 합산해서 브리핑하세요."
    
    return (
        f"[시스템 계산 결과]\n"
        f"현재까지 DB에서 확인된 총 칼로리: {total['칼로리']}kcal\n"
        f"상세 내역:\n{details_joined}"
        f"{instruction}"
    )

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    # 💡 융통성을 발휘하고 찰진 드립을 칠 수 있도록 temperature를 0.6으로 설정
    llm = ChatOpenAI(model="gpt-4o", temperature=0.6, openai_api_key=Config.OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools([calculate_nutrition_tool])
    
    sys_msg = SystemMessage(content=(
        "당신은 능청스럽고 유쾌하며 지식이 풍부한 '천재 끼니탐정'입니다.\n\n"
        "[수사 원칙]\n"
        "1. [자연스러운 브리핑]: 도구(계산기)가 넘겨준 데이터를 바탕으로 자연스럽게 대화하세요. 로봇 같은 기계식 말투('도구 결과에 따르면', '계산기 오류입니다')는 절대 금지입니다.\n"
        "2. [탐정의 폭풍 추론 💡]: 만약 시스템이 'DB 검색 실패'라고 알려준 음식이 있다면, '흠, 마라탕은 공공 DB 수첩엔 없는 최신 용의자군요! 하지만 제 데이터에 따르면...' 이라며 능청스럽게 자체 추정치를 꺼내어 전체 칼로리에 더해서 대답하세요.\n"
        "3. [팩트폭력과 조언]: 유쾌하게 대화를 이끌어주되, 전체 칼로리가 높으면 장난스럽게 과식을 지적하고 가벼운 식단 조언을 건네주세요."
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
