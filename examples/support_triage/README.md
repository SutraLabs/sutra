# Support triage example

```bash
pip install -e .
sutra run examples/support_triage/pipeline.py --text "Need help with the dashboard"
sutra run examples/support_triage/pipeline.py --input examples/support_triage/sample_input.json
```

The pipeline outputs `classification`, `replier`, and `summary` JSON objects.
