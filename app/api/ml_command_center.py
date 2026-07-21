from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.connection import get_db
from app.database.schemas import CommandCenterAssessment
from app.schemas.ml_command_center import (
    CommandCenterAssessmentResponse,
    SensorAssessmentInput,
)
from app.services.anomaly_model_service import get_anomaly_model_service
from app.services.command_center_service import (
    calculate_compound_assessment,
    calculate_worker_exposure,
    check_permit_conflict,
    detect_safety_rules,
)
from app.services.ml_prediction_service import predict_accident_risk
from app.services.model_metrics_service import load_risk_model_metrics

router = APIRouter(
    prefix="/ml-command-center",
    tags=["ML Command Center"],
)


@router.get("/model-metrics")
def get_model_metrics():
    return load_risk_model_metrics()


@router.post(
    "/assess",
    response_model=CommandCenterAssessmentResponse,
)
async def assess_sensor_condition(
    payload: SensorAssessmentInput,
    db: AsyncSession = Depends(get_db),
):
    try:
        data = payload.model_dump()
        if data.get("active_permit") is not None:
            data["active_permit"] = dict(data["active_permit"])

        ml_result = predict_accident_risk(data)

        anomaly_service = get_anomaly_model_service()
        missing_features = [
            column
            for column in anomaly_service.feature_columns
            if column not in data
        ]
        if missing_features:
            raise ValueError(
                "Missing anomaly-model features: "
                + ", ".join(missing_features)
            )

        raw_anomaly_result = anomaly_service.predict(
            {
                column: data[column]
                for column in anomaly_service.feature_columns
            }
        )
        anomaly_result = {
            "available": True,
            "is_anomaly": raw_anomaly_result["is_anomaly"],
            "raw_anomaly_score": raw_anomaly_result["raw_anomaly_score"],
            "anomaly_component_score": raw_anomaly_result["anomaly_score"],
        }

        rule_result = detect_safety_rules(data)
        permit_result = check_permit_conflict(data)
        exposure_result = calculate_worker_exposure(data)
        compound_result = calculate_compound_assessment(
            data=data,
            ml_result=ml_result,
            anomaly_result=anomaly_result,
            rule_result=rule_result,
            permit_result=permit_result,
            exposure_result=exposure_result,
        )

        response: dict[str, Any] = {
            "sensor_ingestion": {
                "status": "accepted",
                "factory": data["factory"],
                "region": data["region"],
                "zone_id": data["zone_id"],
                "timestamp": data["timestamp"],
            },
            "ml_prediction": ml_result,
            "anomaly_detection": anomaly_result,
            "rule_detection": rule_result,
            "permit_conflict": permit_result,
            "worker_exposure": exposure_result,
            "compound_assessment": compound_result,
        }

        encoded_response = jsonable_encoder(response)
        db.add(
            CommandCenterAssessment(
                factory=data["factory"],
                region=data["region"],
                zone_id=data["zone_id"],
                assessed_at=data["timestamp"],
                risk_level=compound_result["risk_level"],
                compound_risk_score=compound_result["compound_risk_score"],
                workers_exposed=exposure_result["workers_exposed"],
                payload=encoded_response,
            )
        )
        await db.commit()
        return response

    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except Exception as error:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"ML assessment failed: {error}",
        ) from error


@router.get("/overview")
async def get_command_center_overview(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(CommandCenterAssessment).order_by(
            CommandCenterAssessment.assessed_at.desc(),
            CommandCenterAssessment.id.desc(),
        )
    )

    latest_by_zone: dict[str, dict[str, Any]] = {}
    for record in result.scalars().all():
        key = f"{record.factory}::{record.region}::{record.zone_id}"
        if key not in latest_by_zone:
            latest_by_zone[key] = record.payload

    regions: list[dict[str, Any]] = []
    for assessment in latest_by_zone.values():
        sensor = assessment["sensor_ingestion"]
        ml = assessment["ml_prediction"]
        anomaly = assessment["anomaly_detection"]
        exposure = assessment["worker_exposure"]
        compound = assessment["compound_assessment"]
        regions.append(
            {
                "factory": sensor["factory"],
                "region": sensor["region"],
                "zone_id": sensor["zone_id"],
                "timestamp": sensor["timestamp"],
                "ml_probability": ml["accident_probability"],
                "is_anomaly": anomaly["is_anomaly"],
                "compound_risk_score": compound["compound_risk_score"],
                "risk_level": compound["risk_level"],
                "workers_exposed": exposure["workers_exposed"],
                "final_decision": compound["final_decision"],
            }
        )

    regions.sort(key=lambda item: item["compound_risk_score"], reverse=True)
    safe_regions = [r for r in regions if r["risk_level"] == "SAFE"]
    alert_regions = [r for r in regions if r["risk_level"] != "SAFE"]

    return {
        "summary": {
            "total_regions": len(regions),
            "safe_regions": len(safe_regions),
            "alert_regions": sum(r["risk_level"] == "ALERT" for r in regions),
            "high_regions": sum(r["risk_level"] == "HIGH" for r in regions),
            "critical_regions": sum(r["risk_level"] == "CRITICAL" for r in regions),
            "workers_exposed": sum(r["workers_exposed"] for r in regions),
        },
        "safe_regions": safe_regions,
        "alert_regions": alert_regions,
        "regions": regions,
    }
