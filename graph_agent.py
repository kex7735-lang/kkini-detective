from typing import Annotated, TypedDict
from langchain_core.messages import SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver 
import json

from nutrition_calculator import NutritionCalculator
from config import Config

calculator = NutritionCalculator()

@tool
def calculate_nutrition_tool(meal_record: str) -> str:
    """
    사용자가 음식을 먹었다고 할 때 실행하여 영양 정보를 확인하는 도구입니다.
    """
    result = calculator.process_meal_record(meal_record)
    
    if result["status"] == "error":
        return f"계산 에러 발생: {result.get('message')}"
        
    details_str = []
    has_missing_food = False
    
    for item in result["details"]:
        if item.get("status") == "not_found":
            has_missing_food = True
            details_str.append(f"\n[용의자 없음] '{item['input_name']}' ({item['quantity']}{item['unit']})")
            details_str.append("- 엑셀 DB에서 아예 단서를 찾지 못했습니다! 탐정의 자체 지식으로 추론해야 합니다.")
        elif item.get("status") == "candidates_found":
            details_str.append(f"\n[용의자 명단] '{item['input_name']}' ({item['quantity']}{item['unit']})")
            for i, cand in enumerate(item["candidates"]):
                nutri = cand['nutrition']
                details_str.append(
                    f"  {i+1}번 후보: {cand['식품명']} (기준 {cand['기준량']}) -> "
                    f"칼로리:{nutri['칼로리']}kcal, 단백질:{nutri['단백질']}g, 지방:{nutri['지방']}g, 탄수화물:{nutri['탄수화물']}g"
                )

    details_joined = "\n".join(details_str)
    
    instruction = (
        "\n\n🚨 [탐정 지시사항]\n"
        "1. [후보 선택]: 각 음식의 '용의자 명단'을 보고 문맥상 가장 적합한 1번 후보(보통 가장 이름이 짧은 기본 음식)를 '당신이 직접 선택'하세요. "
        "(예를 들어 사용자가 '치킨'을 먹었다면 치킨너겟이 아니라 프라이드치킨을 고르세요!)\n"
        "2. [직접 계산]: 당신이 선택한 음식들의 칼로리를 모두 더해서 '오늘 먹은 총 칼로리'를 스스로 계산하세요.\n"
    )
    
    if has_missing_food:
        instruction += "3. [자체 추론]: DB에 없는 음식은 당황하지 말고, 당신의 자체 지식으로 합리적인 칼로리(1인분 기준)를 추정해서 총합에 꼭 포함시키세요!\n"
        
    instruction += "4. [자연스러운 보고]: 기계처럼 '몇 번 후보를 선택했습니다'라고 말하지 말고, 쿨하고 자연스럽게 'ㅇㅇ와 ㅁㅁ를 드셨군요! 총 000kcal입니다'라고 브리핑하세요."

    return (
        f"[시스템 계산 서류철]\n"
        f"{details_joined}"
        f"{instruction}"
    )

class State(TypedDict):
    messages: Annotated[list, add_messages]

def chatbot(state: State):
    # 융통성 있는 대화를 위해 온도(temperature) 상향
    llm = ChatOpenAI(model="gpt-4o", temperature=0.6, openai_api_key=Config.OPENAI_API_KEY)
    llm_with_tools = llm.bind_tools([calculate_nutrition_tool])
    
    sys_msg = SystemMessage(content=(
        "당신은 능청스럽고 유쾌하며 지식이 풍부한 '천재 끼니탐정'입니다.\n\n"
        "[수사 원칙]\n"
        "1. 도구(계산기)가 넘겨준 서류철을 보고 '가장 상식적인 진짜 음식'을 직접 골라내세요.\n"
        "2. 선택한 음식들의 영양성분과 당신이 추론한 음식을 합쳐서 최종 브리핑을 완성하세요.\n"
        "3. 로봇 같은 기계식 말투('서류철에 따르면', '도구의 결과')는 절대 금지입니다.\n"
        "4. 유쾌하게 대화를 이끌어주되, 전체 칼로리가 높으면 장난스럽게 과식을 지적해주세요."
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
