# testchat_v1_answeragent.py
from sutra import Agent

answeragent = Agent(
    name='answeragent',
    objective='To answer general questions in ELI10 format',
    model='llama3.1:latest',
    prompt='''To answer general questions in ELI10 format

Input: {text}

Process the input and return structured JSON.
Be specific and clear in your output.

Return only valid JSON.''',
    expects_json=True,
    output_key='answeragent',
    required_keys=[],
    retries=1,
    temperature=0.1
)