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
    """사용자가 음식을 먹었다고 할 때 실행하여 칼로리를 계산하는 도구입니다."""
    result = calculator.process_meal_record(meal_record)
    
    if result["status"] == "error":
        return f"계산 에러 발생: {result.get('message')}"
        
    total = result["total_nutrition"]
    details_str = []
    for item in result["details"]:
        if item.get("status") == "not_found":
            details_str.append(f"- {item['food_name']} (DB에 정보가 없음)")
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
    llm = ChatOpenAI(model="gpt-4o", temperature=0.5, openai_api_key=Config.OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools([calculate_nutrition_tool])
    
    # 💡 [핵심] 탐정의 컨셉과 말투를 아주 디테일하고 사람 냄새나게 세팅!
    sys_msg = SystemMessage(content=(
        "당신은 능청스럽고 유쾌하면서도 실력은 확실한 '천재 끼니탐정'입니다.\n"
        "로봇 같은 말투('계산기에서 오류가 발생했습니다', '제 원칙에 따라' 등)는 절대 쓰지 말고, 친근하고 센스 있는 사람처럼 말하세요.\n\n"
        "수사 원칙:\n"
        "1. [자연스러운 팩트 브리핑]: 도구(계산기)가 준 결과를 임의로 지어내지 말고 팩트대로 말하되, 자연스러운 대화에 녹여내세요. (예: '수첩을 확인해보니 방금 드신 건 총 OOOkcal네요!')\n"
        "2. [수사 실패 대처]: 도구에서 특정 음식 정보가 'DB에 없음'으로 나오면, 에러라고 딱딱하게 말하지 마세요. 대신 '앗, 제 수사 수첩에 그 음식 정보가 빠져있네요! 혹시 정확한 브랜드명이나 다른 이름으로 알려주시겠어요?'라며 능청스럽게 힌트를 요구하세요.\n"
        "3. [과식 팩트폭력과 조언]: 권장 칼로리를 초과하면 재치 있게 장난스러운 팩트폭력을 날려주고, 칼로리가 남았다면 남은 양에 맞는 가벼운 메뉴를 추천해 주세요."
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
