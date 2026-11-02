# Contributing to Blender Visual Toolkit

BVT welcomes bug reports, documentation improvements, tests and
feature contributions.

## Development flow

```text
develop
→ feature/*
→ tests
→ documentation
→ release gates
```

Before submitting a change:

- keep the working tree focused;
- preserve deterministic generation;
- add or update tests;
- run `python tools/bvt.py regression`;
- run `git diff --check`;
- document public behavior changes;
- verify licenses for new dependencies and assets.

Do not commit generated datasets, local `.tmp` content or release
binaries.

Contributors must have the right to submit all contributed code and
assets.

The project source code is distributed under GPL-3.0-or-later.
