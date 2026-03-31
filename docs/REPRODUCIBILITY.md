# Reproducibility

Evaluation numbers cited in the project README were produced with a **pinned internal harness** (see `eval/harness_version.txt`). Full Docker-based replication—including exact tokenizer revisions, task manifests, and scoring scripts—is scheduled for public release pending legal review.

For early partners, contact the maintainers with your org id to request the replication bundle checksum.

## What you can verify today

- Run `scripts/verify_env.sh` to confirm baseline OS capabilities.
- Run `make check` to validate shell script syntax for shipped tooling.
