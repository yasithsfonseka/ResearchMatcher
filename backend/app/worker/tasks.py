import os
import time
import json
import logging
import redis
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import IngestionJob, Paper
from app.services.embeddings import embed_paper
from app.providers.openalex import OpenAlexProvider
from app.services.deduplication import upsert_provider_paper

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")

r = redis.from_url(settings.REDIS_URL)

def process_ingestion_job(job_id: str, provider: str, query: str):
    db: Session = SessionLocal()
    job = db.query(IngestionJob).filter(IngestionJob.id == job_id).first()
    if not job:
        logger.error(f"Job {job_id} not found")
        db.close()
        return
        
    try:
        job.status = "processing"
        job.progress = 10.0
        db.commit()
        
        if provider == "openalex":
            adapter = OpenAlexProvider()
            import asyncio
            loop = asyncio.get_event_loop()
            papers = loop.run_until_complete(adapter.search_papers(query=query, limit=50))
            
            job.progress = 50.0
            db.commit()
            
            total = len(papers)
            for idx, p in enumerate(papers):
                paper_obj = upsert_provider_paper(db, p)
                embed_paper(db, paper_obj)
                job.progress = 50.0 + (float(idx + 1) / max(total, 1)) * 45.0
                db.commit()

        job.status = "completed"
        job.progress = 100.0
        job.completed_at = time.strftime('%Y-%m-%d %H:%M:%S')
        db.commit()
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        job.status = "failed"
        job.error_summary = str(e)
        db.commit()
    finally:
        db.close()

def run_worker():
    logger.info("Starting ResearchMatch Redis Background Worker...")
    while True:
        try:
            # BLPOP task queue
            item = r.blpop("ingestion_queue", timeout=5)
            if item:
                _, payload = item
                data = json.loads(payload.decode('utf-8'))
                logger.info(f"Processing background task: {data}")
                process_ingestion_job(
                    job_id=data.get("job_id"),
                    provider=data.get("provider", "openalex"),
                    query=data.get("query", "")
                )
        except Exception as e:
            logger.error(f"Worker loop error: {e}")
            time.sleep(2)

if __name__ == "__main__":
    run_worker()
