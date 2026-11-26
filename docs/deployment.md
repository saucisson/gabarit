# Deployment channels (ADR-0008 N3)

Deployment channels are an instance-level concern. The shared
pattern (protected branches, merge-as-deploy, two-channel split,
rollback expectations) has moved to the platform registry:
`saucisson/platform`, consumed per instance through its
`platform-lock.txt` under ADR-0010.

The template itself deploys nothing. An instance that reaches
production writes its deployment decision in its own ADR (>= 0100)
and takes the pattern from the registry at its pin, adapting only
the adaptation boundary.

Rule N3 of `docs/engineering-rules.md` still governs the shape
wherever it applies: a deployment is identified by the commit SHA
it was built from, never by a mutable alias anyone can bump
retroactively.
