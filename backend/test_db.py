from app.database.connection import SessionLocal
from app.models.personnel import Personnel
from app.models.user import User
from app.models.risk_prediction import RiskPrediction
from app.models.recommendation import Recommendation

db = SessionLocal()

u = db.query(User).filter(User.username == 'p1025').first()
p = db.query(Personnel).filter(Personnel.user_id == u.id).first()

pred = db.query(RiskPrediction).filter(RiskPrediction.personnel_id == p.id).order_by(RiskPrediction.created_at.desc()).first()

print(f"Latest prediction ID for p1025: {pred.id if pred else 'None'}")
if pred:
    print(f"Risk Level: {pred.risk_level.value}")
    recs = db.query(Recommendation).filter(Recommendation.risk_prediction_id == pred.id).all()
    print(f"Recommendations found: {len(recs)}")
    for r in recs:
        print(f"- {r.recommendation_text}")

db.close()
