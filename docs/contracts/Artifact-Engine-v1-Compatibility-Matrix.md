# Artifact Engine v1 — Compatibility Matrix

Status: Frozen
Engine version: `artifact-engine-v1`

---

# 1. Purpose

This document freezes provider compatibility behavior for Artifact
Engine v1.

It complements:

- `Artifact-Engine-v1-Freeze.md`;
- provider implementation;
- canonical Artifact Engine v1 acceptance scenario.

Compatibility changes after freeze require an explicit contract
revision.

---

# 2. Provider Matrix

| Artifact | Category | Stage | Order | Target / Input | v1 compatibility |
|---|---|---|---:|---|---|
| `over_exposure` | lighting | pre_render | 100 | Scene exposure | No additional compatibility constraints |
| `reflection` | glass | pre_render | 100 | GLASS / Principled or Glass BSDF | Requires unlinked Roughness input |
| `fingerprints` | glass | pre_render | 110 | GLASS / Principled or Glass BSDF | Requires unlinked Roughness input; compatible with Reflection |
| `condensation` | glass | pre_render | 120 | GLASS / Principled or Glass BSDF | Clean or Fingerprints Roughness; preserves user shader links |
| `frost` | glass | pre_render | 130 | GLASS / Principled or Glass BSDF | Clean, Fingerprints or Condensation Roughness; preserves user shader links |
| `dust` | glass | pre_render | 140 | GLASS / Principled or Glass BSDF | Clean, Fingerprints, Condensation or Frost Roughness; preserves user shader links |
| `water_drops` | glass | pre_render | 150 | GLASS / Principled or Glass BSDF | Clean through Dust Roughness chain; preserves user shader links; Normal untouched |
| `scratches` | glass | pre_render | 160 | GLASS / Principled or Glass BSDF | Clean through Water Drops Roughness chain; preserves user shader links; Normal untouched |
| `motion_blur` | camera | post_render | 50 | RGB/RGBA rendered image | Requires RGB or RGBA image |
| `noise` | sensor | post_render | 100 | RGB/RGBA rendered image | Requires RGB or RGBA image |
| `jpeg_compression` | compression | post_render | 200 | RGB/RGBA rendered image | Requires RGB/RGBA; preserves PNG dataset contract |

---

# 3. Canonical Glass Chain

```text
Reflection
→ Fingerprints
→ Condensation
→ Frost
→ Dust
→ Water Drops
→ Scratches
```

The linked Roughness chain begins with Fingerprints.

Reflection changes the effective roughness before the linked chain and
therefore does not create a dedicated downstream `input_mode`.

---

# 4. Accepted Glass Roughness Inputs

## Reflection

```text
unlinked Roughness
```

## Fingerprints

```text
unlinked Roughness
```

Reflection is compatible because Reflection does not create a linked
Roughness chain.

## Condensation

```text
constant
fingerprints
```

## Frost

```text
constant
fingerprints
condensation
```

## Dust

```text
constant
fingerprints
condensation
frost
```

## Water Drops

```text
constant
fingerprints
condensation
frost
dust
```

## Scratches

```text
constant
fingerprints
condensation
frost
dust
water_drops
```

---

# 5. User Shader Ownership

Artifact Engine v1 must not take ownership of arbitrary user shader
graphs.

For providers that advertise:

```text
preserves_user_shader_links
```

an unrecognized linked Roughness input is preserved and skipped.

The provider must not:

```text
delete the user node
replace the user link
reconnect the user graph incorrectly
claim the node as BVT-owned state
```

Reflection and Fingerprints use the stricter v1 rule:

```text
requires_unlinked_roughness_input
```

Their compatibility contract must not be silently broadened during the
v1 freeze.

---

# 6. Temporary Shader Ownership

The following Glass providers use temporary BVT shader nodes:

```text
Fingerprints
Condensation
Frost
Dust
Water Drops
Scratches
```

Provider-owned temporary nodes must be removable during reset.

Providers using procedural masks must also remove owned temporary image
data during reset.

---

# 7. Procedural Mask Providers

The v1 compatibility metadata explicitly identifies procedural mask
behavior for:

```text
Condensation
Frost
Dust
Water Drops
Scratches
```

These providers do not require external mask assets.

---

# 8. Normal Socket Contract

The frozen explicit compatibility metadata guarantees an untouched
Normal socket for:

```text
Water Drops
Scratches
```

The Scratches lifecycle/RGB acceptance additionally verifies this
behavior.

Any future expansion of the explicit Normal-socket compatibility
contract requires tests and contract revision.

---

# 9. Post-render Chain

Canonical post-render order:

```text
Motion Blur
→ Noise
→ JPEG Compression
```

All three operate after Blender rendering.

JPEG Compression performs encode/decode simulation internally but the
dataset contract remains:

```text
final image format = PNG
```

---

# 10. Compatibility Freeze Rule

After Artifact Engine v1 Freeze, the following require an explicit
contract revision:

```text
accepted upstream provider changes
target material-role changes
supported shader changes
user-link ownership changes
Normal/Bump ownership changes
pre/post-render stage changes
execution-order changes
temporary-resource ownership changes
output-format changes
```

Bug fixes are allowed only when they preserve the frozen compatibility
semantics.

---

# 11. Acceptance Evidence

Compatibility is covered by:

```text
provider compatibility_rules()
artifact lifecycle smoke tests
artifact RGB smoke tests
27/27 regression suite
canonical Artifact Engine v1 acceptance config
canonical decoded-RGBA repeat-run audit
```

The canonical full Glass acceptance path is:

```text
fingerprints
→ condensation
→ frost
→ dust
→ water_drops
→ scratches
```

with all providers applied in one deterministic generation run.
