"""Celery tasks for document processing and Google Fit sync."""

import hashlib
import os
import uuid
from datetime import date, datetime, timedelta
from typing import Optional

from celery import chain, group

from app.core.config import settings
from app.core.database import async_session
from app.core.security import decrypt
from app.models import (
    Biomarker,
    Document,
    HealthMetric,
    MetricSource,
    MetricType,
    ProcessingStatus,
    Recommendation,
    SyncJob,
    SyncJobStatus,
    SyncJobType,
    TestResult,
    User,
)
from app.services.celery_app import celery_app
from app.services.google_fit_service import GoogleFitService
from app.services.llm_service import LLMService, chunk_ocr_text
from app.services.normalization_service import (
    compute_out_of_range,
    convert_unit,
    match_biomarker,
    parse_ref_range,
)
from app.services.ocr_service import OCRService
from app.services.rag_service import RAGService


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def process_document(self, document_id: str):
    """10-step pipeline: fetch → OCR → LLM → normalize → insert → complete."""
    import asyncio

    async def _run():
        session = async_session()
        try:
            # Step 1: Fetch document
            from sqlalchemy import select

            result = await session.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                raise ValueError(f"Document {document_id} not found")
            if not doc.file_path:
                raise ValueError(f"Document {document_id} has no file path")

            # Step 2: OCR
            await _update_status(session, doc, ProcessingStatus.ocr_processing)
            ocr_service = OCRService()
            ocr_result = ocr_service.extract(doc.file_path)
            doc.raw_ocr_text = ocr_result.raw_text
            await session.commit()

            if not ocr_result.raw_text.strip():
                raise ValueError("OCR extracted no text")

            # Step 3: LLM parsing
            await _update_status(session, doc, ProcessingStatus.llm_parsing)
            llm_service = LLMService()
            chunks = chunk_ocr_text(ocr_result.raw_text)
            all_results = []
            for chunk in chunks:
                parsed = await llm_service.parse(chunk)
                all_results.append(parsed)

            # Merge results from all chunks
            merged = _merge_llm_results(all_results)
            doc.llm_json_payload = merged
            doc.lab_name = merged.get("lab_name")
            if merged.get("report_date"):
                try:
                    doc.report_date = date.fromisoformat(merged["report_date"])
                except (ValueError, TypeError):
                    pass
            await session.commit()

            # Step 4: Normalize
            await _update_status(session, doc, ProcessingStatus.normalizing)
            biomakers_list = await _load_biomarkers(session)
            results = merged.get("results", [])

            # Step 5: Insert test results (atomic)
            test_result_ids = []
            async with session.begin():
                for r in results:
                    tr = await _normalize_and_insert(
                        session, doc, r, biomakers_list
                    )
                    if tr:
                        test_result_ids.append(str(tr.id))

            # Step 6: Complete
            doc.processing_status = ProcessingStatus.complete
            await session.commit()

            # Step 7: Auto-delete PDF if configured
            user_result = await session.execute(
                select(User).where(User.id == doc.user_id)
            )
            user = user_result.scalar_one_or_none()
            if user and user.settings_json.get("auto_delete_pdfs"):
                if doc.file_path and os.path.exists(doc.file_path):
                    os.remove(doc.file_path)

            # Step 8: Trigger recommendation generation for out-of-range
            for tr_id in test_result_ids:
                tr_result = await session.execute(
                    select(TestResult).where(TestResult.id == tr_id)
                )
                tr = tr_result.scalar_one_or_none()
                if tr and tr.is_out_of_range:
                    generate_recommendation_for_result.delay(tr_id)

            return {"status": "complete", "results_count": len(test_result_ids)}

        except Exception as e:
            if doc:
                doc.processing_status = ProcessingStatus.failed
                doc.processing_error = str(e)
                await session.commit()
            raise
        finally:
            await session.close()

    return asyncio.run(_run())


async def _update_status(session, doc: Document, status: ProcessingStatus):
    doc.processing_status = status
    await session.commit()


async def _load_biomarkers(session) -> list[dict]:
    from sqlalchemy import select
    result = await session.execute(select(Biomarker))
    return [
        {
            "id": str(b.id),
            "loinc_code": b.loinc_code,
            "display_name": b.display_name,
            "standard_name": b.standard_name,
            "standard_unit": b.standard_unit,
            "aliases": b.aliases or [],
        }
        for b in result.scalars().all()
    ]


async def _normalize_and_insert(
    session, doc: Document, result_item: dict, biomarkers: list[dict]
) -> Optional[TestResult]:
    raw_name = result_item.get("raw_name", "")
    if not raw_name:
        return None

    biomarker_id = match_biomarker(raw_name, biomarkers)
    if not biomarker_id:
        return None

    # Find the matched biomarker
    matched = next((b for b in biomarkers if b["id"] == biomarker_id), None)
    if not matched:
        return None

    # Parse value
    raw_value_str = result_item.get("raw_value_string", "")
    value = result_item.get("value")
    if value is None and raw_value_str:
        try:
            cleaned = raw_value_str.replace("<", "").replace(">", "").replace("H", "").replace("L", "").strip()
            value = float(cleaned)
        except (ValueError, TypeError):
            return None
    if value is None:
        return None

    # Unit conversion
    raw_unit = result_item.get("unit")
    target_unit = matched["standard_unit"]
    raw_value = value
    if raw_unit and raw_unit != target_unit:
        value = convert_unit(value, raw_unit, target_unit, matched["loinc_code"])

    # Reference range parsing
    ref_text = result_item.get("ref_range_text", "")
    ref_low, ref_high = parse_ref_range(ref_text)
    lab_ref_low = result_item.get("ref_range_low")
    lab_ref_high = result_item.get("ref_range_high")
    if lab_ref_low is not None and lab_ref_high is not None:
        ref_low, ref_high = lab_ref_low, lab_ref_high

    # Out of range
    is_oof, direction = compute_out_of_range(value, ref_low, ref_high)

    # Document-level out_of_range_flag overrides
    doc_flag = result_item.get("out_of_range_flag", "").upper()
    if doc_flag in ("H", "HH", "L", "LL"):
        direction_map = {"H": "high", "HH": "high", "L": "low", "LL": "low"}
        direction = direction_map.get(doc_flag, direction)
        if direction != "normal":
            is_oof = True

    report_date = doc.report_date or date.today()

    tr = TestResult(
        id=str(uuid.uuid4()),
        document_id=doc.id,
        user_id=doc.user_id,
        biomarker_id=biomarker_id,
        result_date=report_date,
        value=value,
        raw_value=raw_value,
        raw_unit=raw_unit,
        standard_unit=target_unit,
        ref_range_low=ref_low,
        ref_range_high=ref_high,
        ref_range_text=ref_text,
        is_out_of_range=is_oof,
        out_of_range_direction=direction,
        lab_ref_range_low=lab_ref_low,
        lab_ref_range_high=lab_ref_high,
    )
    session.add(tr)
    return tr


def _merge_llm_results(all_results: list[dict]) -> dict:
    """Merge results from multiple chunks into a single payload."""
    merged = {"lab_name": None, "report_date": None, "patient_info_present": False, "results": []}
    for result in all_results:
        if result.get("lab_name") and not merged["lab_name"]:
            merged["lab_name"] = result["lab_name"]
        if result.get("report_date") and not merged["report_date"]:
            merged["report_date"] = result["report_date"]
        if result.get("patient_info_present"):
            merged["patient_info_present"] = True
        merged["results"].extend(result.get("results", []))
    return merged


@celery_app.task(bind=True, max_retries=2, default_retry_delay=30)
def generate_recommendation_for_result(self, test_result_id: str):
    """Generate RAG-based recommendation for an out-of-range test result."""
    import asyncio

    async def _run():
        session = async_session()
        try:
            from sqlalchemy import select

            result = await session.execute(
                select(TestResult, Biomarker)
                .join(Biomarker, TestResult.biomarker_id == Biomarker.id)
                .where(TestResult.id == test_result_id)
            )
            row = result.one_or_none()
            if not row:
                return

            tr, biomarker = row

            # Retrieve relevant guidelines
            rag = RAGService()
            contexts = await rag.retrieve(
                biomarker_name=biomarker.display_name,
                value=tr.value,
                unit=tr.standard_unit or biomarker.standard_unit,
                direction=tr.out_of_range_direction.value,
                loinc_code=biomarker.loinc_code,
            )

            # Generate recommendation
            text = await rag.generate_recommendation(
                biomarker_name=biomarker.display_name,
                value=tr.value,
                unit=tr.standard_unit or biomarker.standard_unit,
                direction=tr.out_of_range_direction.value,
                ref_low=tr.ref_range_low,
                ref_high=tr.ref_range_high,
                contexts=contexts,
            )

            # Store recommendation
            rec = Recommendation(
                user_id=tr.user_id,
                biomarker_id=biomarker.id,
                test_result_id=tr.id,
                recommendation_text=text,
                rag_context_used=[c[:500] for c in contexts],
            )
            session.add(rec)
            await session.commit()
            return {"recommendation_id": str(rec.id)}

        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

    return asyncio.run(_run())


@celery_app.task(bind=True, max_retries=2, default_retry_delay=60)
def sync_google_fit(self, user_id: str, days_back: int = 30):
    """Celery task for Google Fit sync — scheduled via Celery Beat."""
    import asyncio

    async def _run():
        session = async_session()
        try:
            from sqlalchemy import select
            import httpx

            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if not user or not user.google_oauth_token:
                return {"status": "skipped", "reason": "no token"}

            # Create sync job record
            job = SyncJob(
                user_id=user_id,
                job_type=SyncJobType.google_fit_sync,
                status=SyncJobStatus.running,
                started_at=datetime.utcnow(),
                celery_task_id=self.request.id,
            )
            session.add(job)
            await session.commit()

            # Decrypt tokens
            access_token = decrypt(user.google_oauth_token)
            refresh_token = decrypt(user.google_refresh_token) if user.google_refresh_token else None

            # Determine last sync date
            last_sync = None
            if user.google_token_expiry:
                # Use incremental tracking
                last_result = await session.execute(
                    select(HealthMetric.date)
                    .where(HealthMetric.user_id == user_id, HealthMetric.source == MetricSource.google_fit)
                    .order_by(HealthMetric.date.desc())
                    .limit(1)
                )
                last_date = last_result.scalar_one_or_none()
                if last_date:
                    last_sync = last_date

            # Fetch data
            gf = GoogleFitService()
            metrics = await gf.sync_metrics(access_token, days_back=days_back, last_sync=last_sync)

            # Upsert into health_metrics
            records_synced = 0
            metric_map = {
                "weight_kg": MetricType.weight_kg,
                "steps": MetricType.steps,
                "sleep_hours": MetricType.sleep_hours,
                "resting_heart_rate_bpm": MetricType.resting_heart_rate_bpm,
                "active_minutes": MetricType.active_minutes,
            }

            for metric_type_name, entries in metrics.items():
                if metric_type_name not in metric_map:
                    continue
                mt = metric_map[metric_type_name]
                for entry in entries:
                    stmt = (
                        "INSERT INTO health_metrics (id, user_id, date, metric_type, value, source) "
                        "VALUES (:id, :user_id, :date, :metric_type, :value, :source) "
                        "ON CONFLICT (user_id, date, metric_type) DO UPDATE SET value = :value, source = :source"
                    )
                    from sqlalchemy import text
                    await session.execute(
                        text(stmt),
                        {
                            "id": str(uuid.uuid4()),
                            "user_id": user_id,
                            "date": entry["date"],
                            "metric_type": mt.value,
                            "value": entry["value"],
                            "source": MetricSource.google_fit.value,
                        },
                    )
                    records_synced += 1

            # Update job status
            job.status = SyncJobStatus.complete
            job.completed_at = datetime.utcnow()
            job.records_synced = records_synced
            await session.commit()

            return {"status": "complete", "records_synced": records_synced}

        except Exception as e:
            if 'job' in locals():
                job.status = SyncJobStatus.failed
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                await session.commit()
            raise
        finally:
            await session.close()

    return asyncio.run(_run())
