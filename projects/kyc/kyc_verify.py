# kyc_verify.py
from sutra import Agent

verify = Agent(
    name='verify',
    objective='Based on UK compliance laws, ensure all KYC details are provided',
    model='qwen3:4b',
    prompt='''Based on UK compliance laws, ensure all KYC details are provided

Input: {text}

Process the input and return structured JSON.
Be specific and clear in your output.

Return only valid JSON.''',
    expects_json=True,
    output_key='verify',
    required_keys=[],
    retries=1,
    temperature=0.1
)