# Retail Edge Cases v0.1

Status: Implemented
Milestone: EP4
Schema concept: `bvt-retail-edge-cases-1`

---

## 1. Purpose

EP4 adds deterministic product and scene state mutations to the
Retail Demo without changing the frozen Artifact Engine v1 contract.

The first supported edge cases are:

- Wrong Angle
- Wrong Position
- Empty Slot
- Occlusion

These are structural scene mutations, not image artifacts.

---

## 2. Architecture Boundary

Canonical processing boundary:

```text
Retail Source Scene
        |
        v
Retail Placement / Edge Case Layer
        |
        v
Final Product Scene State
        |
        v
Camera / Lighting
        |
        v
Artifact Engine v1
        |
        v
Render
        |
        v
Annotation / Validation / Export
```

### Placement / Edge Case Layer owns

- product selection;
- slot selection;
- product transforms;
- product presence / absence;
- deliberate product displacement;
- deliberate product rotation;
- deliberate occluder placement;
- before / after product state;
- deterministic reset to baseline state.

### Artifact Engine v1 owns

Only visual or image-level degradation:

- over exposure;
- reflection;
- fingerprints;
- condensation;
- frost;
- dust;
- water drops;
- scratches;
- motion blur;
- noise;
- JPEG compression.

### Rule

Wrong Angle, Wrong Position, Empty Slot and Occlusion MUST NOT be
implemented as Artifact Engine providers.

Artifact Engine v1 remains frozen.

---

## 3. Baseline State

The Beverage Fridge source manifest remains the canonical baseline.

Every frame starts from deterministic baseline state:

```text
slot
  -> sku
  -> instance_id
  -> baseline transform
  -> annotation enabled
```

Before an edge case is applied, all mutable product state MUST be reset.

A frame must never inherit mutation state from the previous frame.

---

## 4. Deterministic Selection

Every edge-case decision MUST derive from:

```text
project seed
+ frame id
+ edge-case namespace
+ target instance / slot identity
```

Selection MUST NOT depend on Python RNG call order.

Canonical strategy:

```text
sha256-namespace-v1
```

Recommended namespaces:

```text
retail-edge-case/wrong-angle
retail-edge-case/wrong-position
retail-edge-case/empty-slot
retail-edge-case/occlusion
```

The same:

```text
seed + config + source scene
```

must reproduce the same selected objects and resulting state.

---

## 5. Wrong Angle

Wrong Angle changes product rotation while preserving its assigned slot.

Owned state:

- selected instance;
- baseline rotation;
- applied rotation;
- axis;
- angle delta.

Minimum v0.1 policy:

- rotate around Z;
- deterministic signed angle;
- no SKU identity change;
- no slot identity change;
- annotation remains enabled.

Example:

```text
0° baseline
-> +22° wrong angle
```

---

## 6. Wrong Position

Wrong Position changes product translation relative to its canonical slot.

Owned state:

- selected instance;
- baseline location;
- applied location;
- displacement vector.

Minimum v0.1 policy:

- bounded X/Y displacement;
- Z remains on shelf surface;
- SKU identity unchanged;
- slot identity unchanged;
- annotation remains enabled.

Wrong Position does not mean assigning the product to another slot.

---

## 7. Empty Slot

Empty Slot removes the product assigned to a selected slot for the frame.

Minimum v0.1 policy:

- slot remains part of scene topology;
- product object is hidden for rendering;
- product is excluded from annotation for that frame;
- source manifest assignment is not destroyed;
- next frame reset restores the product.

The edge-case manifest records the missing slot and original instance.

---

## 8. Occlusion

Occlusion introduces deliberate partial visibility obstruction.

Minimum v0.1 implementation may use a synthetic deterministic occluder.

The occluder:

- is infrastructure, not a SKU;
- is not a YOLO annotation target;
- must have stable deterministic placement;
- must be reset or removed between frames.

Occlusion changes visibility, not product identity.

---

## 9. Annotation Boundary

Annotations are generated from the final scene state after placement and
edge-case mutations.

### Wrong Angle

Product remains annotated.

BBox is calculated from final transformed geometry.

### Wrong Position

Product remains annotated.

BBox is calculated from final transformed geometry.

### Empty Slot

Hidden product produces no YOLO row for that frame.

### Occlusion

Product remains annotated while visible.

The exact visibility / clipping policy is finalized separately inside EP4
before acceptance.

---

## 9.1 BBox / Clipping / Visibility Policy v0.1

EP4 v0.1 uses geometric full-object bounding boxes.

Canonical rules:

- annotation is calculated from the final transformed product geometry;
- Wrong Angle uses the rotated product geometry;
- Wrong Position uses the translated product geometry;
- Empty Slot disables annotation and therefore produces no bbox;
- Occlusion does not shrink the bbox to visible pixels;
- an occluded product keeps its full-object geometric bbox;
- synthetic occluders are never annotation targets;
- projected bbox coordinates are clipped to the image frame;
- normalized YOLO coordinates remain inside `[0, 1]`;
- a bbox with no positive projected area is omitted;
- an object fully behind the camera is omitted;
- EP4 v0.1 does not use a pixel visibility threshold;
- EP4 v0.1 does not produce segmentation-derived visible bboxes.

Therefore:

```text
final structural transform
        |
        v
geometric object bounds
        |
        v
camera projection
        |
        v
image clipping
        |
        v
YOLO bbox
```

Occlusion is intentionally an amodal/full-object annotation policy
for EP4 v0.1.

A future visibility-aware or segmentation-aware policy requires a new
contract version and must not silently change this behavior.

---

## 10. Manifest Contract

Every frame with edge-case processing must expose:

```json
{
  "retail_edge_cases": {
    "version": "retail-edge-cases-v0.1",
    "enabled": true,
    "events": []
  }
}
```

Each event must include at minimum:

```text
edge_case
applied
seed
instance_id or slot_id
before
after
```

Example conceptual record:

```json
{
  "edge_case": "wrong_angle",
  "applied": true,
  "seed": 123,
  "instance_id": "retail:beverage_fridge_v01:shelf_01:slot_001:bev_can_red_330",
  "before": {
    "rotation_z_degrees": 0.0
  },
  "after": {
    "rotation_z_degrees": 22.0
  }
}
```

---

## 11. Per-frame Lifecycle

Canonical lifecycle:

```text
reset baseline
-> derive deterministic seeds
-> select targets
-> apply retail edge cases
-> capture final scene state
-> apply camera / lighting
-> apply Artifact Engine
-> render
-> annotate
-> write manifest
-> validate
```

Reset is mandatory even when the previous frame did not apply an edge case.

---

## 12. Non-goals for EP4

EP4 does not add:

- new Artifact Engine providers;
- planogram compliance scoring;
- OCR;
- GTIN recognition;
- real brand assets;
- business rules for shelf correctness;
- inventory state;
- temporal video simulation;
- physics simulation.

---

## 13. Acceptance Direction

EP4 acceptance must prove:

- deterministic target selection;
- deterministic mutations;
- baseline reset between frames;
- before / after manifest state;
- correct YOLO behavior;
- correct hidden-object behavior;
- correct bbox behavior after transform;
- no regression in Artifact Engine v1;
- no mutation leakage between frames.

---

## 14. Architecture Decision

The canonical boundary is:

```text
STRUCTURAL SCENE STATE
        =
Retail Placement / Edge Cases

VISUAL DEGRADATION
        =
Artifact Engine
```

This boundary is frozen for EP4 implementation.
