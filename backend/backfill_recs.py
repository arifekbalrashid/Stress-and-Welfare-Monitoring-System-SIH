import asyncio
from app.database.connection import init_db
from app.models.personnel import Personnel
from app.models.risk_prediction import RiskPrediction
from app.models.recommendation import Recommendation
from app.services.ml_service import predict_for_personnel

async def main():
    await init_db()
    personnel_list = await Personnel.find().to_list()
    for p in personnel_list:
        pred = await RiskPrediction.find(RiskPrediction.personnel_id == p.id).sort(-RiskPrediction.created_at).first_or_none()
        if pred:
            count = await Recommendation.find(Recommendation.risk_prediction_id == pred.id).count()
            if count == 0:
                print(f"Prediction {pred.id} for personnel {p.service_id} has no recommendations. Generating...")
                try:
                    await predict_for_personnel(p.id)
                    print("Generated successfully.")
                except Exception as e:
                    print(f"Error: {e}")
    print("Done backfilling.")

if __name__ == "__main__":
    asyncio.run(main())
