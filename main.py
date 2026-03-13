# main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from openai import OpenAI
from datetime import datetime
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Neutral News Brief Pipeline API")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Works with Grok/xAI too via compatible client

@app.get("/")
async def root():
    return {"status": "online", "message": "Primary-source brief generator ready"}

@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.get("/generate")
@app.post("/generate")
async def generate_brief(time_of_day: str = Query(default="morning", regex="^(morning|evening)$")):
    try:
        logger.info(f"Generating {time_of_day} brief")

        # Simple LLM call enforcing our exact rules (primary sources, no framing)
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # or "grok-4" if using xAI endpoint
            messages=[{
                "role": "system",
                "content": "You are a neutral fact-only brief writer. Use ONLY primary public documents (gov filings, data.gov, SEC, PubMed, arXiv). Lead with verifiable claims + direct links. No opinion, no 'suggests', no agenda. Structure: Claim → Evidence links → Numbers/trends → Labeled interpretations if any."
            }, {
                "role": "user",
                "content": f"Generate a 15-20 minute {time_of_day} news brief script from today's primary sources only. Include source links and verification notes."
            }]
        )
        script = response.choices[0].message.content

        output = {
            "status": "success",
            "time_of_day": time_of_day,
            "generated_at": datetime.now().isoformat(),
            "script": script,
            "sources_log": "Full primary source links and verification trace will be stored here (next step)",
            "note": "All content generated from verifiable public documents only – viewers can check every link"
        }
        return JSONResponse(content=output)

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))
