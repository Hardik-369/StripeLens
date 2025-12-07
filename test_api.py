
import httpx
import asyncio
import json

async def test_api():
    url = "http://localhost:8005/explain_event"
    
    # Mock Stripe Event: Payment Failed
    mock_event = {
        "id": "evt_123456789",
        "object": "event",
        "type": "invoice.payment_failed",
        "data": {
            "object": {
                "id": "in_12345",
                "object": "invoice",
                "amount_due": 2999,
                "currency": "usd",
                "customer": "cus_987654321",
                "customer_email": "customer@example.com",
                "status": "open",
                "attempt_count": 1,
                "billing_reason": "subscription_cycle"
            }
        }
    }

    print(f"Sending test event: {mock_event['type']}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=mock_event, timeout=60.0)
            
        if response.status_code == 200:
            print("\n[SUCCESS] API Success!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"\n[ERROR] API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"\n[ERROR] Connection Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_api())
