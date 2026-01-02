# Security

- Sutra executes user-provided pipelines and agents. Do not run pipelines from untrusted sources.
- Output traces land in `.sutra/`; delete or rotate this data if it contains sensitive information.
- The CLI does not perform sandboxing; audit any tools called from `steps` before enabling them.
