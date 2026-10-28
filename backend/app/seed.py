"""
Seed script — creates demo users, personnel, units, and 6 months of time-series data in MongoDB.
Run: python -m app.seed
"""

import asyncio
import random
from datetime import datetime, date, timedelta
from app.database.connection import init_db
from app.models.user import User, UserRole
from app.models.unit import Unit
from app.models.personnel import Personnel, ReviewStatus
from app.models.operational_data import OperationalData
from app.models.wellness_checkin import WellnessCheckin
from app.models.risk_prediction import RiskPrediction, RiskLevel, RiskTrend
from app.models.recommendation import Recommendation
from app.models.intervention import Intervention, InterventionType, InterventionStatus
from app.models.consent import Consent, ConsentDataType, ConsentStatus
from app.models.support_request import SupportRequest, SupportCategory, SupportStatus
from app.models.audit_log import AuditLog
from app.models.model_version import ModelVersion, ModelStatus
from app.auth.password import hash_password

random.seed(42)


async def seed():
    print("Initializing MongoDB connection...")
    await init_db()

    print("Clearing MongoDB collections...")
    for model in [
        User, Unit, Personnel, OperationalData, WellnessCheckin,
        RiskPrediction, Recommendation, Intervention, Consent,
        SupportRequest, AuditLog, ModelVersion
    ]:
        await model.delete_all()

    print("Seeding MongoDB...")

    # ---- Units ----
    units = [
        Unit(name="12th Battalion", location="Srinagar", type="battalion"),
        Unit(name="7th Company", location="Imphal", type="company"),
        Unit(name="Central Station", location="Delhi", type="station"),
    ]
    for u in units:
        await u.insert()

    # ---- System users ----
    admin_user = User(username="admin", email="admin@saathi.gov.in", password_hash=hash_password("admin1234"), role=UserRole.ADMIN)
    wo_user = User(username="wo_sharma", email="wo.sharma@saathi.gov.in", password_hash=hash_password("demo1234"), role=UserRole.WELFARE_OFFICER, assigned_unit_id=units[0].id)
    cmd_user = User(username="cmd_singh", email="cmd.singh@saathi.gov.in", password_hash=hash_password("demo1234"), role=UserRole.COMMANDER, assigned_unit_id=units[0].id)

    await admin_user.insert()
    await wo_user.insert()
    await cmd_user.insert()

    units[0].commander_user_id = cmd_user.id
    await units[0].save()

    # ---- Personnel ----
    personnel_data = [
        ("p1024", "Rajesh",  "Kumar",   "Constable",      units[0].id, "2018-03-15"),
        ("p1025", "Amit",    "Verma",   "Head Constable",  units[0].id, "2015-07-22"),
        ("p1026", "Suresh",  "Yadav",   "Constable",      units[1].id, "2019-11-01"),
        ("p1027", "Deepak",  "Sharma",  "ASI",            units[1].id, "2012-06-10"),
        ("p1028", "Manoj",   "Singh",   "Constable",      units[2].id, "2020-01-20"),
        ("p1029", "Vikram",  "Patel",   "Head Constable",  units[2].id, "2016-09-05"),
        ("p1030", "Arun",    "Gupta",   "Constable",      units[0].id, "2021-04-12"),
        ("p1031", "Sanjay",  "Mishra",  "SI",             units[0].id, "2010-08-30"),
        ("p1032", "Ravi",    "Chauhan", "Constable",      units[1].id, "2022-02-14"),
        ("p1033", "Pradeep", "Joshi",   "Constable",      units[2].id, "2017-12-01"),
    ]

    personnel_records = []
    for sid, fname, lname, rank, uid, doj in personnel_data:
        u = User(username=sid, email=f"{sid}@saathi.gov.in", password_hash=hash_password("demo1234"), role=UserRole.PERSONNEL)
        await u.insert()
        p = Personnel(
            user_id=u.id,
            unit_id=uid,
            service_id=sid,
            first_name=fname,
            last_name=lname,
            rank=rank,
            date_of_joining=date.fromisoformat(doj)
        )
        await p.insert()
        personnel_records.append(p)

    # ---- Model version ----
    mv = ModelVersion(
        model_type="xgboost",
        version_tag="v1.0",
        feature_set_version="v1",
        metrics={"precision": 0.84, "recall": 0.79, "f1": 0.81, "auc": 0.88},
        status=ModelStatus.ACTIVE,
        artifact_path="ml/artifacts/xgboost_v1.pkl",
        trained_at=datetime(2026, 3, 1),
    )
    await mv.insert()

    # ---- Risk profiles per personnel (defines trajectory over 6 months) ----
    profiles = {
        "p1024": (45, +5.0, 4, 3),    # 6 months (Mar-Aug)
        "p1025": (30, -2.0, 3, 5),    # 4 months (May-Aug)
        "p1026": (50, +1.0, 5, 8),    # 1 month (Aug only)
        "p1027": (35, +0.5, 3, 3),    # 6 months
        "p1028": (20, +0.0, 2, 8),    # 1 month
        "p1029": (60, -3.0, 4, 4),    # 5 months
        "p1030": (40, +3.0, 5, 7),    # 2 months
        "p1031": (25, +0.0, 2, 8),    # 1 month
        "p1032": (55, +2.0, 4, 3),    # 6 months
        "p1033": (38, -1.5, 3, 8),    # 1 month
    }

    # Generate 6 months of data (March–August 2026)
    months = []
    for m in range(3, 9):
        month_start = date(2026, m, 1)
        if m == 8:
            month_end = date(2026, 8, 31)
        else:
            month_end = date(2026, m + 1, 1) - timedelta(days=1)
        months.append((month_start, month_end))

    feature_labels = {
        "duty_hours":           ("Duty hours per week", "Long duty hours"),
        "night_shifts":         ("Night shifts per month", "Frequent night shifts"),
        "consecutive_duty_days":("Consecutive duty days", "Extended continuous duty"),
        "rest_hours":           ("Rest hours per day", "Insufficient rest"),
        "deployment_days":      ("Deployment duration (days)", "Extended deployment"),
        "leave_gap_days":       ("Days since last leave", "Extended leave gap"),
    }

    rec_templates = {
        "leave":    ["Leave review recommended — {val}-day gap since last leave", "Consider approving pending leave request"],
        "workload": ["Consider workload redistribution for current duty cycle", "Shift handoff review recommended"],
        "rest":     ["Shift rotation adjustment may improve recovery", "Recommend minimum 8-hour rest between duties"],
        "deployment": ["Deployment rotation review recommended", "Consider relief rotation schedule"],
    }

    for pi, p in enumerate(personnel_records):
        sid = p.service_id
        base_score, trend_dir, volatility, start_month = profiles[sid]

        prev_score = None
        personnel_months = [(m_start, m_end) for m_start, m_end in months if m_start.month >= start_month]

        for mi, (m_start, m_end) in enumerate(personnel_months):
            score_at_month = base_score + trend_dir * mi + random.uniform(-volatility, volatility)
            score_at_month = max(5, min(95, score_at_month))

            risk_factor = score_at_month / 100
            duty_hours = round(40 + risk_factor * 25 + random.uniform(-3, 3), 1)
            night_shifts = int(2 + risk_factor * 8 + random.uniform(-1, 1))
            consec_days = int(5 + risk_factor * 15 + random.uniform(-2, 2))
            rest_hours = round(8 - risk_factor * 4 + random.uniform(-0.5, 0.5), 1)
            deploy_days = int(risk_factor * 60 + random.uniform(-5, 5))
            leave_gap = int(15 + risk_factor * 70 + random.uniform(-5, 5))

            od = OperationalData(
                personnel_id=p.id,
                period_start=m_start, period_end=m_end,
                duty_hours=max(35, duty_hours),
                night_shifts=max(0, night_shifts),
                consecutive_duty_days=max(1, consec_days),
                rest_hours=max(2, rest_hours),
                deployment_days=max(0, deploy_days),
                leave_gap_days=max(0, leave_gap),
                training_hours=round(random.uniform(0, 8), 1),
                source="csv_import",
            )
            await od.insert()

            has_wellness = random.random() < 0.7
            if has_wellness:
                inv_factor = 1 - risk_factor
                wc = WellnessCheckin(
                    personnel_id=p.id,
                    sleep_quality=max(1, min(5, round(1 + inv_factor * 4 + random.uniform(-0.5, 0.5)))),
                    energy_level=max(1, min(5, round(1 + inv_factor * 4 + random.uniform(-0.5, 0.5)))),
                    workload_score=max(1, min(5, round(1 + risk_factor * 4 + random.uniform(-0.5, 0.5)))),
                    wellbeing_score=max(1, min(5, round(1 + inv_factor * 4 + random.uniform(-0.5, 0.5)))),
                    recovery_score=max(1, min(5, round(1 + inv_factor * 4 + random.uniform(-0.5, 0.5)))),
                    submitted_at=datetime(m_start.year, m_start.month, random.randint(10, 25), random.randint(9, 18))
                )
                await wc.insert()

            risk_score = round(score_at_month, 1)
            if risk_score <= 30:
                risk_level = RiskLevel.LOW
            elif risk_score <= 50:
                risk_level = RiskLevel.MODERATE
            elif risk_score <= 75:
                risk_level = RiskLevel.ELEVATED
            else:
                risk_level = RiskLevel.HIGH

            if prev_score is None:
                trend = RiskTrend.STABLE
            elif risk_score > prev_score + 3:
                trend = RiskTrend.INCREASING
            elif risk_score < prev_score - 3:
                trend = RiskTrend.DECREASING
            else:
                trend = RiskTrend.STABLE
            prev_score = risk_score

            feature_impacts = {
                "duty_hours": max(0, (duty_hours - 45) / 100),
                "night_shifts": max(0, (night_shifts - 3) / 30),
                "consecutive_duty_days": max(0, (consec_days - 7) / 40),
                "rest_hours": max(0, (6 - rest_hours) / 20),
                "deployment_days": max(0, deploy_days / 150),
                "leave_gap_days": max(0, (leave_gap - 20) / 200),
            }
            top_features = sorted(feature_impacts.items(), key=lambda x: x[1], reverse=True)[:4]
            shap_factors = {
                "factors": [
                    {"feature": f, "label": feature_labels[f][1], "impact": round(v + random.uniform(0, 0.05), 3)}
                    for f, v in top_features if v > 0.01
                ]
            }

            pred = RiskPrediction(
                personnel_id=p.id,
                risk_score=risk_score,
                risk_level=risk_level,
                trend=trend,
                shap_factors=shap_factors,
                confidence=round(0.65 + random.uniform(0, 0.25), 2),
                model_version_id=mv.id,
                has_wellness_data=has_wellness,
                created_at=datetime(m_start.year, m_start.month, 28, 12, 0),
            )
            await pred.insert()

            if risk_level in (RiskLevel.ELEVATED, RiskLevel.HIGH):
                rec_cats = []
                if leave_gap > 40:
                    rec_cats.append(("leave", rec_templates["leave"][0].format(val=leave_gap)))
                if duty_hours > 50:
                    rec_cats.append(("workload", random.choice(rec_templates["workload"])))
                if rest_hours < 5:
                    rec_cats.append(("rest", random.choice(rec_templates["rest"])))
                if deploy_days > 30:
                    rec_cats.append(("deployment", random.choice(rec_templates["deployment"])))

                for pri, (cat, text) in enumerate(rec_cats[:3], 1):
                    rec = Recommendation(
                        risk_prediction_id=pred.id,
                        category=cat,
                        recommendation_text=text,
                        priority=pri
                    )
                    await rec.insert()

            if m_start.month == 8:
                if risk_level == RiskLevel.HIGH:
                    p.review_status = ReviewStatus.UNDER_REVIEW
                elif risk_level == RiskLevel.ELEVATED:
                    p.review_status = random.choice([ReviewStatus.NEEDS_REVIEW, ReviewStatus.MONITORING])
                elif risk_level == RiskLevel.MODERATE and trend == RiskTrend.INCREASING:
                    p.review_status = ReviewStatus.NEEDS_REVIEW
                else:
                    p.review_status = ReviewStatus.CLOSED
                await p.save()

    # ---- Consent for all personnel ----
    for p in personnel_records:
        await Consent(
            personnel_id=p.id,
            data_type=ConsentDataType.WELLNESS_CHECKIN,
            status=ConsentStatus.GRANTED,
            granted_at=datetime(2026, 3, 1)
        ).insert()

        if random.random() < 0.7:
            await Consent(
                personnel_id=p.id,
                data_type=ConsentDataType.RISK_SHARING,
                status=ConsentStatus.GRANTED,
                granted_at=datetime(2026, 3, 1)
            ).insert()

    # ---- Sample intervention ----
    p1024_preds = await RiskPrediction.find(
        RiskPrediction.personnel_id == personnel_records[0].id
    ).sort(-RiskPrediction.created_at).to_list()

    p1024_pred = p1024_preds[1] if len(p1024_preds) > 1 else (p1024_preds[0] if p1024_preds else None)
    if p1024_pred:
        iv = Intervention(
            personnel_id=personnel_records[0].id,
            welfare_officer_id=wo_user.id,
            risk_prediction_id=p1024_pred.id,
            intervention_type=InterventionType.LEAVE_RECOMMENDATION,
            notes="Recommended 10 days leave. Personnel has not taken leave in 63+ days.",
            status=InterventionStatus.COMPLETED,
            follow_up_date=date(2026, 8, 15),
            created_at=datetime(2026, 7, 29, 14, 30),
        )
        await iv.insert()

    # ---- Sample Support Requests ----
    support_data = [
        (personnel_records[0], SupportCategory.LEAVE, "I haven't been able to take leave for over 2 months. My family needs me at home. Requesting leave approval assistance.", SupportStatus.SUBMITTED),
        (personnel_records[2], SupportCategory.WORKLOAD, "Duty hours have been very high this month. Feeling exhausted. Requesting workload redistribution.", SupportStatus.SUBMITTED),
        (personnel_records[4], SupportCategory.HEALTH, "Having persistent back pain from extended field duty. Need to schedule a medical check-up.", SupportStatus.ACKNOWLEDGED),
        (personnel_records[6], SupportCategory.PERSONAL, "Going through a difficult situation at home. Would like to speak to a counselor confidentially.", SupportStatus.IN_PROGRESS),
        (personnel_records[8], SupportCategory.WORKLOAD, "Night shift rotation seems uneven. Some of us are doing more night shifts than others. Can this be reviewed?", SupportStatus.SUBMITTED),
        (personnel_records[1], SupportCategory.LEAVE, "My leave request has been pending for 3 weeks with no response. Need urgent clarification.", SupportStatus.RESOLVED),
    ]

    for p, cat, desc, status in support_data:
        sr = SupportRequest(
            personnel_id=p.id,
            category=cat,
            description=desc,
            status=status,
            assigned_to=wo_user.id if status != SupportStatus.SUBMITTED else None,
            created_at=datetime(2026, 8, random.randint(5, 28), random.randint(8, 18), random.randint(0, 59)),
        )
        await sr.insert()

    print("Done. Seeded 13 users + 10 personnel × 6 months of time-series data into MongoDB.")


if __name__ == "__main__":
    asyncio.run(seed())
