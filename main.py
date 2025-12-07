import os
import json
import logging
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

import uvicorn
import httpx
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field



# ====================================================
# 🔧 CONFIGURATION
# ====================================================

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Environment Variables
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
# Using the free open-source model as requested
OPENROUTER_MODEL = "amazon/nova-2-lite-v1:free" 



# ====================================================
# 📝 MODELS
# ====================================================

class EventExplanation(BaseModel):
    event_type: str = Field(..., description="The type of the Stripe event")
    summary: str = Field(..., description="Human-readable explanation of what happened")
    root_cause: str = Field(..., description="The underlying reason for the event")
    customer_impact_level: str = Field(..., description="Impact level: low, medium, or high")
    recommended_actions: List[str] = Field(..., description="List of recommended next steps")

# ====================================================
# 🧠 CORE ANALYTICS LOGIC
# ====================================================

async def analyze_stripe_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes a raw Stripe webhook event using OpenRouter LLM.
    Returns a structured dictionary with explanation and recommendations.
    """
    
    # 1. Extract Metadata
    event_type = event.get("type", "unknown_type")
    data_object = event.get("data", {}).get("object", {})
    
    # Extract ID for reference, but we pass the whole object to LLM
    object_id = data_object.get("id", "unknown_id")
    
    logger.info(f"Analyzing event: {event_type} (ID: {object_id})")

    # 2. Build LLM Prompts
    system_prompt = (
        "You are an expert Stripe technical consultant and business analyst. "
        "Your goal is to parse raw JSON webhook events and translate them into "
        "clear, actionable insights for a non-technical stakeholder.\n\n"
        "RULES:\n"
        "1. Output valid JSON ONLY. No markdown, no commentary.\n"
        "2. Be concise but specific. Avoid generic advice like 'check logs'.\n"
        "3. Derive impact level conservatively: failures/disputes are HIGH, "
        "warnings/upcoming invoices are LOW/MEDIUM.\n"
        "4. 'root_cause' should explain the technical reason (e.g., 'Insufficient funds', 'Expired card')."
    )

    # Summarize essential info to help the LLM focus, though we also send the full event
    # (Truncating very large events might be necessary in production, but we'll send raw for now as requested)
    event_str = json.dumps(event, indent=2)

    user_prompt = f"""
Analyze the following Stripe webhook event.

Event Type: {event_type}

Raw Payload:
{event_str}

OUTPUT INSTRUCTIONS:
1. 'summary': Provide a 1-sentence executive summary of what happened.
2. 'root_cause': Extract the specific failure code or reason if present (e.g., 'generic_decline', 'insufficient_funds'). If success, state "Successful transaction".
3. 'customer_impact_level':
   - HIGH: Payment failed, dispute created, subscription canceled unexpectedly.
   - MEDIUM: Payment dispute won, subscription updated.
   - LOW: Payout paid, invoice created, payment succeeded.
4. 'recommended_actions': 
   - Propose 2-3 specific steps.
   - Example 1: "Contact customer [email/ID] to update payment method."
   - Example 2: "Review dispute evidence for charge [ID]."

Output STRICT JSON matching this schema:
{{
  "event_type": "{event_type}",
  "summary": "...",
  "root_cause": "...",
  "customer_impact_level": "low | medium | high",
  "recommended_actions": ["..."]
}}
"""

    # 3. Call OpenRouter API
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost",
        "X-Title": "StripeEventExplainer",
        "Content-Type": "application/json"
    }

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.2, # Low temperature for consistent, structured output
    }

    try:
        if not OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY not set. Using fallback logic immediately.")
            raise ValueError("Missing API Key")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_BASE_URL,
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            
            result_json = response.json()
            content = result_json["choices"][0]["message"]["content"]
            
            # Attempt to clean potential markdown formatting if the model disobeys
            cleaned_content = content.replace("```json", "").replace("```", "").strip()
            
            parsed_result = json.loads(cleaned_content)
            
            # normalized validation of impact level
            if "customer_impact_level" in parsed_result:
                parsed_result["customer_impact_level"] = parsed_result["customer_impact_level"].lower()
                if parsed_result["customer_impact_level"] not in ["low", "medium", "high"]:
                     parsed_result["customer_impact_level"] = "medium" # default to medium if invalid
            
            return parsed_result

    except Exception as e:
        logger.error(f"LLM analysis failed: {str(e)}")

        # 4. Fallback Logic (Risk Level Mapping)
        impact = "medium"
        if "payment_failed" in event_type:
            impact = "high"
        elif "dispute" in event_type:
            impact = "high"
        elif "invoice.upcoming" in event_type:
            impact = "low"
        
        fallback_response = {
            "event_type": event_type,
            "summary": f"Received event {event_type}. Automated analysis unavailable.",
            "root_cause": "N/A (LLM unavailable)",
            "customer_impact_level": impact,
            "recommended_actions": ["Check Stripe Dashboard manually."]
        }
        return fallback_response

# ====================================================
# 🚀 FASTAPI APP
# ====================================================

app = FastAPI(title="Stripe Event Explainer")



@app.post("/explain_event", response_model=EventExplanation)
async def explain_event(request: Request):
    """
    Endpoint to process Stripe webhooks.
    """
    try:
        body = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    result = await analyze_stripe_event(body)
    return result



# ====================================================
# 🏁 APP RUNNER
# ====================================================

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
