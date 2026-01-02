# kyc_pipeline.py
# verify customer ID and proof of address

from sutra import Step, Pipeline
import importlib

AGENT_ORDER = ["kyc_reader", "kyc_verify"]

def build():
    steps = []
    prev = ['text']
    
    for agent_file in AGENT_ORDER:
        mod = importlib.import_module(agent_file)
        agent_name = agent_file.split('_')[-1]
        agent = getattr(mod, agent_name)
        steps.append(Step(agent, takes=prev.copy()))
        prev.append(agent_name)
    
    return Pipeline(steps)

DEFAULT_INPUT = {'text': 'test input'}
