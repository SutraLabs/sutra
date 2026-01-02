# dogfood_reviewer.py
from sutra import Agent

reviewer = Agent(
    name='reviewer',
    objective='Apply UK Gambling Commission rules to the consolidated customer profile and output the compliance verdict.',
    model='qwen3:4b',
    prompt='''You are the compliance reviewer. You receive the original case text plus structured attributes from the informer agent (available in {informer}).

Assess affordability, source-of-funds risk, citizenship constraints, and any AML red flags. Produce JSON with this shape:
{{
  "verdict": "approve|manual_review|reject",
  "summary": "One paragraph describing the reasoning in plain English.",
  "breach_rules": ["List specific UKGC or internal policy rules that might be breached"],
  "recommended_actions": ["Additional checks, documents, or escalations required"]
}}

Rules:
- Choose verdict=manual_review when information is incomplete but not clearly disqualifying.
- Only cite breach_rules that are justified by the given facts.
- recommended_actions should be actionable (e.g., "Request proof of income for last 3 months").

Input: {text}

Return ONLY valid JSON matching the schema above.''',
    expects_json=True,
    output_key='reviewer',
    required_keys=["verdict", "summary", "breach_rules", "recommended_actions"],
    retries=1,
    temperature=0.1
)
