import asyncio
from app.database.connection import init_db
from app.models.personnel import Personnel
from app.models.user import User
from app.models.risk_prediction import RiskPrediction
from app.models.recommendation import Recommendation

async def main():
    await init_db()
    u = await User.find_one(User.username == "p1025")
    if not u:
        print("User p1025 not found")
        return
    p = await Personnel.find_one(Personnel.user_id == u.id)
    if not p:
        print("Personnel for p1025 not found")
        return

    pred = await RiskPrediction.find(RiskPrediction.personnel_id == p.id).sort(-RiskPrediction.created_at).first_or_none()

    print(f"Latest prediction ID for p1025: {pred.id if pred else 'None'}")
    if pred:
        print(f"Risk Level: {pred.risk_level.value}")
        recs = await Recommendation.find(Recommendation.risk_prediction_id == pred.id).to_list()
        print(f"Recommendations found: {len(recs)}")
        for r in recs:
            print(f"- {r.recommendation_text}")

if __name__ == "__main__":
    asyncio.run(main())
