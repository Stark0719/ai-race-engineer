from openai import OpenAI
from dotenv import load_dotenv
import json

from agent.tools import strategy_tool
from agent.rag import retrieve_context


load_dotenv()
client = OpenAI()


def chat_with_engineer(user_message, driver_code, base_lap_time):

    tools = [
        {
            "type": "function",
            "function": {
                "name": "strategy_tool",
                "description": "Run race strategy simulation and return recommended strategy with confidence.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "pit_loss_time": {"type": "number"},
                        "safety_car_prob": {"type": "number"},
                        "iterations": {"type": "number"}
                    },
                    "required": ["pit_loss_time", "safety_car_prob", "iterations"]
                }
            }
        }
    ]
    
    context = retrieve_context(user_message)
    if context.strip():
        system_prompt = (
            "You are a professional race strategy engineer. "
            "If the user asks about pit loss, safety car probability, "
            "or strategy comparison, you MUST call the strategy_tool. "
            "Use the following knowledge when relevant:\n\n"
            f"{context}"
        )
    else:
        system_prompt = (
            "You are a professional race strategy engineer. "
            "If the user asks about pit loss, safety car probability, "
            "or strategy comparison, you MUST call the strategy_tool."
        )
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"You are a professional race strategy engineer. Use the following knowledge when relevant:\n\n{context}"},
            {"role": "user", "content": user_message}
        ],
        tools=tools,
        tool_choice="auto"
    )

    message = response.choices[0].message

    if message.tool_calls:

        tool_call = message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)

        decision = strategy_tool(
            driver_code=driver_code,
            total_laps=57,
            base_lap_time=base_lap_time,
            pit_loss_time=args["pit_loss_time"],
            safety_car_prob=args["safety_car_prob"],
            iterations=int(args["iterations"])
        )

        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"You are a professional race strategy engineer. Use the following knowledge when relevant:\n\n{context}"},
                {"role": "user", "content": user_message},
                message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": "strategy_tool",
                    "content": json.dumps(decision)
                }
            ]
        )

        return second_response.choices[0].message.content

    return message.content
