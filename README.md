# TrainSmart 🏃

An agentic AI running coach that generates personalized weekly training plans using an LLM reasoning loop and tool calling.

## How it works

TrainSmart uses an agentic loop powered by the OpenAI API. When you submit a runner profile, the model autonomously decides which tools to call, executes them in sequence, and reasons over the structured results before generating a training plan — no hardcoded control flow or prompt templates.

**Agentic loop flow:**
1. User submits a runner profile via `POST /plan`
2. The agent determines which tools it needs
3. It calls `calculate_target_mileage` to compute a safe peak mileage using the 10% rule
4. It calls `calculate_pace_zones` to derive easy, tempo, and interval paces
5. It reasons over both tool results and generates a structured 7-day plan
6. The loop exits when the model stops issuing tool calls and returns a final response

**Tools available to the agent:**
- `calculate_target_mileage` - applies the 10% rule to compute a safe peak mileage given your race goal and timeline
- `calculate_pace_zones` - derives easy, tempo, and interval pace zones based on your experience level

## Tech Stack

- **Python** + **FastAPI**
- **OpenAI API** (GPT-4o) with function/tool calling
- **Pydantic** for request validation
- **pytest** + **unittest.mock** for unit and integration tests
- **Docker** for containerization

## Getting Started

### Prerequisites
- Python 3.9+
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))
- Docker (optional)

### Run locally

```bash
git clone https://github.com/sophie97yang/trainsmart.git
cd trainsmart

cp .env.example .env
# add your OPENAI_API_KEY to .env

pip install -r requirements.txt
python3 -m uvicorn main:app --reload
```

### Run with Docker

```bash
docker build -t trainsmart .
docker run -p 8000:8000 --env-file .env trainsmart
```

### Run tests

```bash
pip install pytest pytest-asyncio
python3 -m pytest test_trainsmart.py -v
```

## API

### `POST /plan`

Generate a weekly training plan.

**Request body:**
```json
{
  "weekly_mileage": 20,
  "goal_race": "half marathon",
  "weeks_until_race": 12,
  "experience_level": "intermediate"
}
```

**Sample response:**
```json
{
  "plan": "Based on your current fitness and 12 weeks until race day, here's your training plan for the week:\n\n**Monday — Rest**\nFull rest or light stretching. Recovery is part of the plan.\n\n**Tuesday — Easy Run: 4 miles**\nPace: 9:00–10:30/mile. Keep it conversational — if you can't hold a sentence, slow down.\n\n**Wednesday — Tempo Run: 3 miles**\nWarm up 1 mile easy, then 2 miles at tempo pace (7:45–8:30/mile). Cool down with 5 min of walking.\n\n**Thursday — Easy Run: 3 miles**\nPace: 9:00–10:30/mile. Focus on form and breathing.\n\n**Friday — Rest or Cross-Training**\nSwim, bike, or yoga. Keep heart rate low.\n\n**Saturday — Long Run: 8 miles**\nPace: 9:30–10:30/mile. This is your most important run of the week — go slow and finish strong.\n\n**Sunday — Rest**\nYou earned it.\n\n**Weekly total: 18 miles**\nYou're safely below your current weekly volume while building your aerobic base. Next week we'll increase by 10%."
}
```

Interactive API docs available at `http://localhost:8000/docs`.

## Project Structure

```
trainsmart/
├── main.py              # FastAPI app and route definitions
├── coach.py             # Agent logic, tool definitions, and agentic loop
├── test_trainsmart.py   # Unit and integration tests
├── requirements.txt
├── Dockerfile
└── .env.example
```

## Future Improvements

- **Strava integration** - pull real activity data via OAuth instead of relying on user-provided input
- **Persistent training history** - store plans and completed runs in PostgreSQL to enable week-over-week adaptation
- **Plan adjustment** - allow the agent to modify an existing plan based on feedback ("that long run felt too hard")
- **Injury risk scoring** - compute acute:chronic workload ratio (ACWR) from historical data and surface warnings before generating a plan
