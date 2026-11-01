# Artifact Engine v1 — Freeze Contract

Status: Frozen
Milestone: EP2
Engine version: `artifact-engine-v1`

---

# 1. Purpose

This document freezes the public and internal behavioral contract of
Artifact Engine v1 before Retail Demo development begins.

After this contract is accepted:

- new artifact categories are frozen until Retail Demo v0.1;
- provider execution semantics must remain backward compatible;
- seed behavior must remain deterministic;
- manifest behavior must remain stable;
- provider lifecycle must remain stable.

Bug fixes are allowed if they preserve the frozen contract.

---

# 2. Provider Registry v1

Artifact Engine v1 contains exactly 11 providers.

## Pre-render

| Order | Artifact ID | Category |
|---:|---|---|
| 100 | `over_exposure` | `lighting` |
| 100 | `reflection` | `glass` |
| 110 | `fingerprints` | `glass` |
| 120 | `condensation` | `glass` |
| 130 | `frost` | `glass` |
| 140 | `dust` | `glass` |
| 150 | `water_drops` | `glass` |
| 160 | `scratches` | `glass` |

## Post-render

| Order | Artifact ID | Category |
|---:|---|---|
| 50 | `motion_blur` | `camera` |
| 100 | `noise` | `sensor` |
| 200 | `jpeg_compression` | `compression` |

No new provider is part of Artifact Engine v1 after freeze.

---

# 3. Canonical Execution Order

Provider execution is sorted by:

```text
stage
execution_order
artifact_id
```

Stage order:

```text
pre_render  = 0
post_render = 1
```

Canonical complete artifact record order:

```text
over_exposure
reflection
fingerprints
condensation
frost
dust
water_drops
scratches
motion_blur
noise
jpeg_compression
```

`over_exposure` and `reflection` both resolve to execution order `100`.

Their deterministic order is therefore resolved by `artifact_id`:

```text
over_exposure
reflection
```

This tie-break behavior is part of Artifact Engine v1.

---

# 4. Provider Base API

Every v1 provider implements the `ArtifactProvider` contract.

Required provider identity fields:

```text
artifact_id
category
description
stage
execution_order
```

Core methods:

```text
validate_config(config)

capture(scene)

apply(
    scene,
    context,
    baseline,
)

reset(
    scene,
    baseline,
)

compatibility_rules()

manifest_export(
    context,
    applied,
    metadata=None,
)
```

Post-render providers additionally use:

```text
apply_post_render(
    scene,
    image_path,
    context,
    baseline,
)
```

The default `apply_post_render()` implementation rejects providers that
do not implement post-render execution.

`preview()` uses the same pre-render provider behavior as `apply()`.

---

# 5. ArtifactConfig Contract

Resolved provider configuration:

```text
artifact_id
enabled
probability
intensity
options
```

Generic constraints:

```text
0 <= probability <= 1
0 <= intensity <= 1
```

Supported stages:

```text
pre_render
post_render
```

Execution order must be a non-negative integer.

---

# 6. ArtifactContext Contract

Per-frame deterministic context:

```text
config
frame_seed
artifact_seed
decision_roll
```

Providers must not obtain artifact randomness from global RNG state.

---

# 7. Lifecycle Contract

Before dataset generation BVT captures a baseline for every registered
provider.

Before each generated frame:

```text
restore_artifacts()
```

is executed.

Pre-render providers then apply against the restored baseline.

After rendering, post-render providers process the image.

At generation cleanup all providers are reset in reverse provider
registration order.

Expected lifecycle:

```text
capture
→ restore clean baseline
→ pre-render apply
→ render
→ post-render apply
→ manifest
→ restore
```

Providers must not leak temporary Blender state between frames.

---

# 8. Reset Contract

Reset occurs in reverse provider registration order.

For the Glass chain this means:

```text
scratches
→ water_drops
→ dust
→ frost
→ condensation
→ fingerprints
→ reflection
→ original material state
```

Provider reset must restore state captured by `capture()`.

Temporary nodes/images owned by a provider must be removed.

Arbitrary user-owned shader links must not be deleted.

---

# 9. Seed Contract

Frame seed strategy:

```text
FRAME_SEED_STRATEGY = sha256-v1
```

Frame seed:

```text
derive_frame_seed(
    base_seed,
    frame_index,
)
```

Frame indices begin at `1`.

Subseed strategy:

```text
SUBSEED_STRATEGY = sha256-namespace-v1
```

Generic subseed:

```text
derive_subseed(
    parent_seed,
    namespace,
    identity="",
)
```

Artifact seed:

```text
derive_subseed(
    frame_seed,
    "artifact",
    artifact_id,
)
```

Artifact decision:

```text
random.Random(
    artifact_seed
).random()
```

Artifact application rule:

```text
enabled
and decision_roll < probability
```

Required property:

```text
same seed + same configuration
→ same artifact decision and artifact state
```

Different provider RNG call counts must not affect another provider.

---

# 10. Canonical Artifact Manifest Record

Every provider exports:

```text
artifact
category
description
stage
execution_order
enabled
probability
intensity
options
seed
decision_roll
applied
affected_objects
affected_camera
affected_materials
parameters
compatibility_rules
```

Provider-specific data belongs inside:

```text
parameters
```

The canonical artifact seed belongs only at:

```text
record["seed"]
```

and should not be duplicated inside provider parameters.

---

# 11. Artifact Engine Manifest Wrapper

Per-frame Artifact Engine output:

```text
enabled
version
artifacts
```

Frozen engine version:

```text
artifact-engine-v1
```

If Artifact Engine is disabled:

```text
enabled   = false
version   = artifact-engine-v1
artifacts = []
```

---

# 12. Dataset Reproducibility Metadata

Dataset manifest currently records:

```text
generation.seed
generation.frame_count
generation.frame_seed_strategy
```

Frame seed strategy is therefore externally visible and frozen for v1.

Artifact records contain their resolved artifact seed.

## Canonical image reproducibility

Artifact Engine v1 image reproducibility is defined by the decoded image
content, not by byte-for-byte equality of the PNG container.

Required repeat-run acceptance:

```text
manifest bytes identical
YOLO label bytes identical
decoded RGBA pixels identical
decoded RMSE = 0
decoded max error = 0
```

Exact PNG file SHA256 equality is not part of the v1 reproducibility
contract.

Blender may write different PNG metadata/container payloads while the
decoded pixel content remains exactly identical.

The dataset format itself remains:

```text
PNG
```

---

# 13. Glass Compatibility Chain

Canonical Glass roughness chain:

```text
Reflection
→ Fingerprints
→ Condensation
→ Frost
→ Dust
→ Water Drops
→ Scratches
```

Glass providers target:

```text
material role = GLASS
```

Supported shader targets:

```text
BSDF_PRINCIPLED
BSDF_GLASS
```

Later Glass providers wrap accepted upstream BVT Roughness links rather
than replacing the chain.

Arbitrary non-BVT user Roughness links must be preserved/skipped by
providers that advertise that compatibility behavior.

---

# 14. Glass Input Compatibility

Canonical accepted linked input progression:

```text
fingerprints:
    clean roughness

condensation:
    clean
    fingerprints

frost:
    clean
    fingerprints
    condensation

dust:
    clean
    fingerprints
    condensation
    frost

water_drops:
    clean
    fingerprints
    condensation
    frost
    dust

scratches:
    clean
    fingerprints
    condensation
    frost
    dust
    water_drops
```

Reflection modifies effective roughness before the linked Glass chain
and does not require a dedicated linked `input_mode`.

---

# 15. Post-render Contract

Post-render ordering:

```text
Motion Blur
→ Noise
→ JPEG Compression
```

Post-render providers operate on the rendered image.

The final dataset image remains PNG even when JPEG Compression internally
performs JPEG encode/decode simulation.

---

# 16. Public Generic Artifact Controls

The stable generic public control model is:

```text
Enabled
Probability
Intensity
```

Provider-specific options may exist where already present in v1.

Adding new generic controls requires a future Artifact Engine contract
revision.

---

# 17. Freeze Rules

After Artifact Engine v1 Freeze:

Allowed:

```text
bug fixes
performance improvements
test improvements
documentation improvements
internal refactors that preserve behavior
```

Requires explicit contract revision:

```text
new artifact provider
provider removal
provider ID rename
category change
stage change
execution order change
seed strategy change
decision algorithm change
manifest field removal/rename
lifecycle semantic change
compatibility semantic change
```

New artifact types are frozen until Retail Demo v0.1.

---

# 18. Acceptance

Artifact Engine v1 Freeze requires:

```text
provider registry audit PASS
provider ordering audit PASS
base API audit PASS
seed strategy audit PASS
manifest schema audit PASS
compatibility audit PASS
canonical acceptance dataset PASS
decoded RGBA repeat-run audit PASS
full regression PASS
package validation PASS
clean Blender profile install PASS
```

Current regression baseline:

```text
TOTAL=27
PASS=27
FAIL=0
```

---

# 19. Freeze Exit Criteria

EP2 is complete when:

- [x] provider registry is frozen;
- [x] execution order is frozen;
- [x] provider API/lifecycle is frozen;
- [x] seed/subseed rules are frozen;
- [x] compatibility matrix is frozen;
- [x] artifact manifest schema is frozen;
- [x] canonical acceptance config exists;
- [x] Artifact Engine documentation is updated;
- [x] Backlog is synchronized;
- [x] package passes;
- [x] clean Blender profile install passes;
- [x] no new artifact providers are allowed before Retail Demo v0.1.
