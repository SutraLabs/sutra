# dogfood_informer.py
from sutra import Agent

informer = Agent(
    name='informer',
    objective='Gather all due-diligence attributes about the bettor and normalize them for downstream checks.',
    model='qwen3:4b',
    prompt='''You are the intake agent in a customer due-diligence pipeline. Read the provided case notes and extract the bettor's key attributes.

Return JSON with this exact shape:
{{
  "full_name": "First Last",
  "residence": "City, Country",
  "citizenships": ["Country"],
  "monthly_deposits_gbp": "Numeric string, e.g. 5000",
  "risk_flags": ["brief descriptions of anything unusual"]
}}

Rules:
- If a field is unknown, set it to "" for strings or [] for lists.
- Reflect only facts present in the text. Do not invent values.
- risk_flags should be empty when no concerns exist.

Input: {text}

Return ONLY valid JSON matching the schema above.''',
    expects_json=True,
    output_key='informer',
    required_keys=["full_name", "residence", "citizenships", "monthly_deposits_gbp", "risk_flags"],
    retries=1,
    temperature=0.1
)
