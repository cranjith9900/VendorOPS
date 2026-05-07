# SAP Adapter Agents

This workspace now has a separate agent implementation and LangGraph orchestration layer:

- `sap_agents/`: reusable validator, enrichment, mapping, and bank intelligence agents.
- `sap_langgraph/`: graph wiring and a dependency-light `run_pipeline()` helper.

The rule-only path runs without API keys. Anthropic and LangGraph are optional: install those packages and set `ANTHROPIC_API_KEY` when you want fallback LLM behavior for missing tax types, ambiguous addresses, or unmapped SAP values.

```powershell
python -m pip install -r requirements-agents.txt
```

```powershell
python -m pytest tests/test_agent_pipeline.py
```

Minimal usage:

```python
from sap_langgraph import run_pipeline

state = run_pipeline(
    {
        "vendor_name": "Acme Ltd",
        "email": "ap@acme.example",
        "tax_id": "US-12345",
        "country": "United States",
        "payment_terms": "net 30",
        "tax_code": "standard",
        "routing_number": "021000021",
        "bank_account": "1234567890",
    }
)

print(state.data["sap"])
```
