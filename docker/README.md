# Docker

Build context must be the **repository root** so `agi` can be copied:

From the repository root:

```bash
docker build -f docker/Dockerfile -t agi-cli:local .
```

This is intended for smoke tests only; performance characteristics differ from bare-metal interactive sessions.
