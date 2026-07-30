# INPUT6 independent consumer

This directory consumes the `rfreel.T0.normalize_identifier` primitive from a separate repository.

## Dependency identity

- producer: `rfreel/T0`
- immutable producer commit: `9a855b13ba4d0340265d57a5fc6d1b132e792c07`
- semantic contract: `1.0.0`
- admission: commit pin + SHA-256 verification + consumer contract tests + external CI

The dependency is fetched only from the immutable commit recorded in `dependency.lock.json`. Branch names are not trusted as version identifiers.

## Novel downstream task

The consumer canonicalizes and deduplicates externally supplied keys. Its held-out examples include the Kelvin sign, German sharp S, circled digits, and invisible format-character rejection.

## Run

```bash
python fetch_dependency.py
python -m unittest discover -s tests -v
python observe_consequence.py
```

## Upgrade policy

A proposed update must:

1. match declared content hashes;
2. preserve the versioned producer contract;
3. pass all consumer-specific tests;
4. pass external GitHub Actions CI.

A failed update does not move the stable pin. The consumer reports the failure to the producer and records the candidate commit as revoked when appropriate.

## Rollback

Restore `producer_commit` and file hashes in `dependency.lock.json` to the last passing immutable commit. The consumer's revocation gate blocks any commit listed in `revoked_commits` before network retrieval.
