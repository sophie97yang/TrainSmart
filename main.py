from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from coach import generate_plan

app = FastAPI(title="TrainSmart Running Coach")


class RunnerProfile(BaseModel):
    weekly_mileage: float       # current avg miles per week
    goal_race: str              # e.g. "5K", "half marathon", "marathon"
    weeks_until_race: int
    experience_level: str       # "beginner", "intermediate", "advanced"


@app.post("/plan")
async def get_plan(profile: RunnerProfile):
    try:
        plan = await generate_plan(profile.model_dump())
        return {"plan": plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
