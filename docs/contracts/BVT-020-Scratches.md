# BVT-020 — Deterministic Scratches Artifact

Status: Contract Frozen
Target branch: `feature/scratches-artifact`

---

# 1. Goal

Implement deterministic procedural scratches on BVT glass materials.

Scratches completes the Artifact Engine v1 Glass pack before the
Artifact Engine freeze and transition to the Retail Demo workstream.

---

# 2. Provider Contract

```text
artifact_id       = scratches
category          = glass
stage             = pre_render
execution_order   = 160
```

Execution order:

```text
Reflection
→ Fingerprints
→ Condensation
→ Frost
→ Dust
→ Water Drops
→ Scratches
→ Render
```

Post-render artifacts continue after rendering:

```text
Motion Blur
→ Noise
→ JPEG Compression
```

---

# 3. Public UI Contract

Public controls for v1:

```text
Enabled
Probability
Intensity
```

Defaults:

```text
enabled      = false
probability  = 0.50
intensity    = 0.50
```

No public Count / Length / Width / Depth / Density controls in v1.

Those parameters remain internal deterministic implementation details.

They may become public in a future version without changing the base
ArtifactProvider API.

---

# 4. Target

Only materials with:

```text
material role = GLASS
```

Supported shader nodes:

```text
BSDF_PRINCIPLED
BSDF_GLASS
```

Only the `Roughness` socket is modified.

The following must remain untouched:

```text
Normal
Bump
Geometry
Object transforms
Annotation
Bounding boxes
```

---

# 5. Visual Model

Scratches should look like sparse glass surface damage:

- thin elongated lines;
- mostly hairline scratches;
- occasional medium scratches;
- rare longer scratches;
- varying direction;
- varying length;
- slight variation in width;
- slight variation in mask strength;
- optional subtle multi-segment curvature;
- sparse coverage;
- no dense noise field;
- visually distinct from Dust;
- visually distinct from Frost;
- visually distinct from Water Drops.

The result must resemble surface scratching rather than cracks.

Cracks / broken glass are outside v1 scope.

---

# 6. Mask

Mask type:

```text
procedural
deterministic
no external assets
```

Resolution:

```text
SCRATCHES_MASK_RESOLUTION = 256
```

Initial internal scratch count:

```text
SCRATCHES_COUNT = 32
```

The exact count is not a public API contract.

Mask channels:

```text
RGB   = white
Alpha = scratch mask
```

Expected approximate coverage:

```text
0 < coverage < 0.10
```

The implementation should normally remain substantially below 10%.

---

# 7. Internal Scratch Distribution

Initial deterministic v1 distribution:

```text
mostly short / hairline
some medium
rare long
```

Suggested normalized length ranges:

```text
short   = 0.04 .. 0.10
medium  = 0.10 .. 0.20
long    = 0.20 .. 0.35
```

Suggested distribution:

```text
short   ≈ 70%
medium  ≈ 25%
long    ≈ 5%
```

Width should stay visually narrow.

Intensity must control artifact strength, not random call order.

---

# 8. Roughness Model

Scratches v1 is roughness-only.

Internal target:

```text
SCRATCHES_ROUGHNESS_TARGET = 0.72
```

For mask value `m` and intensity `i`:

```text
strength = m * i

output_roughness =
    current_roughness * (1 - strength)
    + SCRATCHES_ROUGHNESS_TARGET * strength
```

The implementation must wrap the current BVT roughness chain instead of
replacing it.

---

# 9. Seed Contract

Artifact seed:

```text
derive_subseed(
    frame_seed,
    "artifact",
    "scratches",
)
```

Material seed:

```text
derive_subseed(
    artifact_seed,
    "artifact-scratches",
    material.name_full,
)
```

Mask layout seed:

```text
derive_subseed(
    material_seed,
    "scratches-mask",
    "layout",
)
```

Mask shape seed:

```text
derive_subseed(
    material_seed,
    "scratches-mask",
    "shape",
)
```

Requirements:

```text
same seed + same config → same mask
different seed          → different mask
```

Random call-order coupling is not allowed.

---

# 10. Accepted Roughness Inputs

Scratches must support:

```text
constant
fingerprints
condensation
frost
dust
water_drops
```

`reflection` does not require a special input mode because it currently
changes the effective constant roughness before the linked Glass chain.

The main full-chain case is:

```text
input_mode = water_drops
```

---

# 11. Arbitrary User Shader Links

If the target Roughness socket already contains a link that is not a
recognized BVT upstream node:

```text
preserve
skip
do not replace
do not delete
```

BVT must not take ownership of arbitrary user shader graphs.

---

# 12. Runtime Shader Nodes

Temporary nodes must use the prefix:

```text
BVT Scratches
```

Suggested nodes:

```text
BVT Scratches Coordinates
BVT Scratches Mask
BVT Scratches Strength
BVT Scratches One Minus
BVT Scratches Target Roughness
BVT Scratches Base Roughness
BVT Scratches Roughness Mix
```

Temporary image prefix:

```text
BVT_Scratches_
```

---

# 13. Reset Contract

Reset order is reverse execution order:

```text
Scratches
→ Water Drops
→ Dust
→ Frost
→ Condensation
→ Fingerprints
→ Reflection
→ original
```

After reset:

```text
temporary Scratches nodes  = 0
temporary Scratches images = 0
original Roughness restored exactly
arbitrary user links preserved
Normal unchanged
```

---

# 14. Manifest Contract

Artifact record uses the canonical Artifact Engine manifest.

Required Scratches parameters when applied:

```text
target_role
mask_resolution
scratch_count
roughness_target
effective_strength
mean_coverage
mean_mask_value
material_changes
```

Each material change should include:

```text
material
material_seed
layout_seed
shape_seed
scratch_count
coverage
mean_mask_value
nodes
```

Each node change should include enough information to verify:

```text
node
input_mode
upstream_node
base_roughness
input_roughness
roughness_target
```

Artifact seed remains in the canonical top-level:

```text
record["seed"]
```

not duplicated inside `parameters`.

---

# 15. Compatibility Contract

Scratches compatibility metadata must state:

```text
target_role = GLASS
roughness_only = true
normal_socket_untouched = true
procedural_mask = true
temporary_shader_nodes = true
arbitrary_user_links = preserve/skip
```

Accepted upstream providers:

```text
fingerprints
condensation
frost
dust
water_drops
```

---

# 16. Source Isolation Test

The procedural mask module must:

```text
compile without Blender
not import bpy
be deterministic
return 256x256 mask
return scratch metadata
```

Required deterministic checks:

```text
same_seed_equal=True
different_seed_changed=True
```

---

# 17. Lifecycle Smoke

Create:

```text
tests/scratches_lifecycle_smoke.py
```

Required input modes:

```text
water_drops
dust
frost
condensation
fingerprints
constant
```

Required checks:

```text
same seed identical
different seed changed
user shader link preserved
Normal socket untouched
roughness restored
temporary nodes removed
temporary images removed
```

---

# 18. Real RGB Smoke

Create:

```text
tests/scratches_artifact_smoke.py
```

Full Glass chain:

```text
Reflection
→ Fingerprints
→ Condensation
→ Frost
→ Dust
→ Water Drops
→ Scratches
```

Required checks:

```text
Scratches applied = true
input_mode = water_drops
real RGB difference > tolerance
same seed repeat RGB identical
bbox unchanged
labels unchanged
Normal untouched
material restored
cleanup complete
```

---

# 19. Headless E2E

Create:

```text
configs/scratches-e2e.json
```

Generate:

```text
10 frames
fixed geometry
fixed camera
fixed lighting
only Scratches enabled
Probability = 1
Intensity = 1
GLASS material
```

Expected:

```text
10 images
10 labels
10 manifest frames
10 unique artifact seeds
10 unique material seeds
more than 1 unique image hash
1 unique label content
input_mode = constant
validation PASS
```

---

# 20. Regression Contract

Current baseline:

```text
25 smoke tests
```

BVT-020 adds:

```text
scratches_lifecycle_smoke.py
scratches_artifact_smoke.py
```

Expected final regression:

```text
TOTAL=27
PASS=27
FAIL=0
BVT_REGRESSION=OK
```

Existing artifact smoke tests must explicitly keep:

```text
artifact_scratches_enabled = False
```

where their isolated contract requires Scratches to remain disabled.

Full artifact order becomes:

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

---

# 21. Package Acceptance

Required before merge:

```text
python tools/bvt.py regression
python tools/bvt.py dataset --config configs/scratches-e2e.json
python tools/bvt.py package
git diff --check
```

All commands must pass.

---

# 22. Definition of Done

BVT-020 is complete only when:

- [ ] contract committed;
- [ ] procedural mask implemented;
- [ ] provider implemented;
- [ ] Engine integrated;
- [ ] Project Properties integrated;
- [ ] UI integrated;
- [ ] manifest contract implemented;
- [ ] lifecycle smoke passes;
- [ ] RGB smoke passes;
- [ ] full regression is 27/27;
- [ ] 10-frame CLI E2E passes;
- [ ] package validation passes;
- [ ] Backlog updated;
- [ ] feature branch merged into `develop`.

After BVT-020:

> Artifact Engine v1 enters freeze and EP2 begins.
