import asyncio
from app.database.connection import SessionLocal
from app.services.ml_service import run_batch_prediction
from app.models.recommendation import Recommendation

db = SessionLocal()

print("Running batch predictions with AI recommendations...")
res = run_batch_prediction(db)
print(res)

recs = db.query(Recommendation).order_by(Recommendation.id.desc()).limit(10).all()
print(f"Generated AI recommendations:")
for r in recs:
    print(f"- [{r.category}] {r.recommendation_text}")

db.close()
