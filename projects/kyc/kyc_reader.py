# kyc_reader.py
from sutra import Agent

reader = Agent(
    name='reader',
    objective='read and understand the data for kyc as input in JSON format.',
    model='qwen3:4b',
    prompt='''read and understand the data for kyc as input in JSON format.

Input: {text}

Process the input and return structured JSON.
Be specific and clear in your output.

Return only valid JSON.''',
    expects_json=True,
    output_key='reader',
    required_keys=[],
    retries=1,
    temperature=0.1
)