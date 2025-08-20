import os
from marketing_tool.celery import app 
from . import models 
from django.db import transaction  
import json 
from openai import OpenAI
from celery.utils.log import get_task_logger
from .naver_crawler.orchestrator import Orchestrator
logger = get_task_logger(__name__)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY")) 


@app.task(bind=True, max_retries=3, default_retry_delay=20)
def scrape_naver_task(self, search_query, search_id:int):
    instance = Orchestrator(search_query, search_id)

    if not instance.run():
        logger.error("Failed to scrape Naver.")
        self.retry()
    else:
        logger.info("Successfully scraped Naver.")


@app.task(bind=True, max_retries=2, default_retry_delay=10)
def run_llm_analysis_task(self, result_item_id: int):
    logger.info("Running LLM analysis for result item %s", result_item_id)
    qs = models.AnalysisResult.objects.filter(result_item=result_item_id)
    result_item = models.ResultItem.objects.get(id=result_item_id)

    for ar in qs:
        try:
            ar.status = models.AnalysisStatusChoices.IN_PROGRESS
            ar.save(update_fields=["status"])

            result_item.analysis_status = models.AnalysisStatusChoices.IN_PROGRESS
            result_item.save(update_fields=["analysis_status"])

            # Normalize result_json -> dict
            if isinstance(ar.result_json, str):
                payload = json.loads(ar.result_json or "{}")
            elif isinstance(ar.result_json, dict) or ar.result_json is None:
                payload = ar.result_json or {}
            else:
                payload = {}

            image_urls = payload.get("image_urls", []) or []

            print(f"Image URLs: {image_urls}")

            input_images = [{"type": "input_image", "image_url": u} for u in image_urls]

            resp = client.responses.create(
                model="gpt-5",  # or your chosen model
                input=[{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": ar.prompt_used or "describe the image"},
                        *input_images
                    ]
                }]
            )

            payload["analysis"] = getattr(resp, "output_text", None)

            # Save back in the same type as the field
            if isinstance(ar._meta.get_field("result_json"), models.models.JSONField):
                ar.result_json = payload
            else:
                ar.result_json = json.dumps(payload, ensure_ascii=False)

            ar.status = models.AnalysisStatusChoices.COMPLETED
            ar.save(update_fields=["result_json", "status"])
            result_item.analysis_status = models.AnalysisStatusChoices.COMPLETED
            result_item.save(update_fields=["analysis_status"])

        except Exception as e:
            ar.status = models.AnalysisStatusChoices.FAILED
            ar.save(update_fields=["status"])

            result_item.analysis_status = models.AnalysisStatusChoices.FAILED
            result_item.save(update_fields=["analysis_status"])
            raise

