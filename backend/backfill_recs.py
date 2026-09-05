from app.database.connection import SessionLocal
from app.models.risk_prediction import RiskPrediction
from app.models.recommendation import Recommendation
from app.services.ml_service import predict_for_personnel
from sqlalchemy import func

db = SessionLocal()

# Find latest predictions that have 0 recommendations
subquery = db.query(
    RiskPrediction.personnel_id,
    func.max(RiskPrediction.created_at).label('max_date')
).group_by(RiskPrediction.personnel_id).subquery()

latest_preds = db.query(RiskPrediction).join(
    subquery,
    (RiskPrediction.personnel_id == subquery.c.personnel_id) &
    (RiskPrediction.created_at == subquery.c.max_date)
).all()

for pred in latest_preds:
    recs_count = db.query(Recommendation).filter(Recommendation.risk_prediction_id == pred.id).count()
    if recs_count == 0:
        print(f"Prediction {pred.id} for personnel {pred.personnel_id} has no recommendations. Generating...")
        try:
            predict_for_personnel(pred.personnel_id, db)
            print("Generated successfully.")
        except Exception as e:
            print(f"Error: {e}")

db.close()
print("Done backfilling.")
