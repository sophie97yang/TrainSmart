from dotenv import load_dotenv
load_dotenv()
import json
import os
from openai import AsyncOpenAI

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Tools the agent can call ---

tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate_target_mileage",
            "description": "Calculates a safe weekly mileage target based on current mileage and race goal. Applies the 10% rule to avoid injury.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_mileage": {"type": "number", "description": "Current weekly mileage in miles"},
                    "weeks_until_race": {"type": "integer", "description": "Number of weeks until the goal race"},
                    "goal_race": {"type": "string", "description": "The target race distance"}
                },
                "required": ["current_mileage", "weeks_until_race", "goal_race"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_pace_zones",
            "description": "Calculates training pace zones (easy, tempo, interval) based on the runner's experience and current fitness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "weekly_mileage": {"type": "number", "description": "Current weekly mileage"},
                    "experience_level": {"type": "string", "description": "beginner, intermediate, or advanced"}
                },
                "required": ["weekly_mileage", "experience_level"]
            }
        }
    }
]


# --- Tool implementations ---

def calculate_target_mileage(current_mileage: float, weeks_until_race: int, goal_race: str) -> dict:
    race_mileage_targets = {
        "5k": 25,
        "10k": 35,
        "half marathon": 45,
        "marathon": 55
    }
    target = race_mileage_targets.get(goal_race.lower(), 30)

    # Cap weekly increase at 10% (standard injury prevention rule)
    max_reachable = current_mileage * (1.10 ** weeks_until_race)
    recommended_peak = min(target, max_reachable)

    return {
        "recommended_peak_mileage": round(recommended_peak, 1),
        "weekly_increase": "10% max per week",
        "taper_week_mileage": round(recommended_peak * 0.6, 1)
    }


def calculate_pace_zones(weekly_mileage: float, experience_level: str) -> dict:
    # Rough pace zone estimates based on mileage/experience
    base_paces = {
        "beginner": {"easy": "11:00-12:30", "tempo": "9:30-10:30", "interval": "8:30-9:30"},
        "intermediate": {"easy": "9:00-10:30", "tempo": "7:45-8:30", "interval": "7:00-7:45"},
        "advanced": {"easy": "7:30-9:00", "tempo": "6:30-7:15", "interval": "5:45-6:30"}
    }
    zones = base_paces.get(experience_level.lower(), base_paces["intermediate"])
    return {"pace_zones_per_mile": zones, "note": "Adjust based on how you feel — easy runs should feel conversational"}


def handle_tool_call(name: str, args: dict) -> str:
    if name == "calculate_target_mileage":
        result = calculate_target_mileage(**args)
    elif name == "calculate_pace_zones":
        result = calculate_pace_zones(**args)
    else:
        result = {"error": f"Unknown tool: {name}"}
    return json.dumps(result)


# --- Agent loop ---

async def generate_plan(profile: dict) -> str:
    system_prompt = """You are an expert running coach. When given a runner's profile, use your tools
to calculate their target mileage and pace zones, then generate a practical 7-day training plan for the upcoming week.

Format the plan clearly with each day, the workout type, distance, and pace zone.
Be specific and encouraging. Keep it concise."""

    user_message = f"""Here is my profile:
- Current weekly mileage: {profile['weekly_mileage']} miles
- Goal race: {profile['goal_race']}
- Weeks until race: {profile['weeks_until_race']}
- Experience level: {profile['experience_level']}

Please calculate my target mileage and pace zones, then build me a training plan for this week."""

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    # Agentic loop — keeps going until the model stops calling tools
    while True:
        response = await client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        message = response.choices[0].message
        messages.append(message)

        if message.tool_calls:
            for tool_call in message.tool_calls:
                args = json.loads(tool_call.function.arguments)
                result = handle_tool_call(tool_call.function.name, args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # No more tool calls — return the final response
            return message.content
