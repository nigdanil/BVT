# Synthetic SKU v0.1 Contract

Status: Implemented
Milestone: EP3
Schema version: `bvt-sku-1`

---

# 1. Purpose

This contract defines the identity and metadata model for synthetic
retail products used by BVT.

A SKU describes a product class.

A SKU does not describe a physical occurrence of that product in a
scene.

---

# 2. Identity Model

Three identities must remain separate:

```text
sku_id
class identity
instance_id
```

## sku_id

Stable identifier of the synthetic product.

Example:

```text
bev_can_red_330
```

Requirements:

```text
lowercase
ASCII
snake_case
stable across scenes
unique within the SKU pack
```

---

## class identity

BVT v0.1 Retail Demo uses one annotation class per synthetic SKU.

Required fields:

```text
class_id
class_name
```

Example:

```text
class_id   = 0
class_name = bev_can_red_330
```

`class_id` must remain stable inside a frozen SKU pack.

`class_name` should normally equal `sku_id`.

---

## instance_id

`instance_id` identifies one physical product occurrence in a scene.

It is not stored as the SKU identity.

Canonical Retail Demo format:

```text
retail:<scene_id>:<shelf_id>:<slot_id>:<sku_id>
```

Example:

```text
retail:beverage_fridge_v01:shelf_01:slot_003:bev_can_red_330
```

The same SKU may therefore have many instance IDs.

---

# 3. Geometry Coordinate Contract

Blender units:

```text
meters
```

Axes:

```text
X = width / shelf horizontal axis
Y = depth
Z = up
```

Product front direction:

```text
-Y
```

Geometry origin:

```text
bottom-center of package footprint
```

This allows placement code to position a package directly onto a shelf
surface using its local origin.

---

# 4. Dimensions

Canonical dimensions:

```text
width_m
depth_m
height_m
```

All dimensions must be strictly positive.

Dimensions describe the intended physical package size after template
scaling.

---

# 5. Geometry Templates

Initial EP3 target templates:

```text
can
bottle
carton
box
```

Template IDs are stable logical IDs.

SKU metadata references a template rather than embedding Blender object
names as the product contract.

Example:

```text
geometry_template = can
```

The actual Blender implementation may use reusable meshes or generated
geometry.

---

# 6. Required SKU Fields

Canonical v0.1 record:

```json
{
  "schema_version": "bvt-sku-1",
  "sku_id": "bev_can_red_330",
  "class_id": 0,
  "class_name": "bev_can_red_330",
  "display_name": "Synthetic Red Can 330",
  "package_type": "can",
  "geometry_template": "can",
  "dimensions": {
    "width_m": 0.066,
    "depth_m": 0.066,
    "height_m": 0.115
  },
  "visual": {
    "base_color": [0.8, 0.1, 0.1, 1.0],
    "texture": null
  },
  "annotation": {
    "enabled": true
  },
  "provenance": {
    "type": "synthetic",
    "attribution_required": false
  }
}
```

---

# 7. Required Fields

Required:

```text
schema_version
sku_id
class_id
class_name
display_name
package_type
geometry_template
dimensions
visual
annotation
provenance
```

---

# 8. Package Type

Initial supported package types:

```text
can
bottle
carton
box
```

`package_type` describes retail semantics.

`geometry_template` describes the geometry implementation.

They may currently have the same value but remain separate concepts.

---

# 9. Visual Contract

`visual` contains appearance metadata.

v0.1 fields:

```text
base_color
texture
```

`base_color`:

```text
RGBA
4 numeric values
0..1
```

`texture` may be:

```text
null
```

or a relative path inside:

```text
examples/retail_demo/textures/
```

No absolute machine-specific paths are allowed.

---

# 10. Annotation Contract

v0.1:

```json
{
  "enabled": true
}
```

Scene construction maps SKU metadata to existing BVT object metadata:

```text
class_id
class_name
instance_id
annotation_enabled
```

No duplicate annotation schema is introduced inside the core engine.

---

# 11. Provenance

Public reference SKU assets should default to:

```text
type = synthetic
attribution_required = false
```

Real trademarks and proprietary packaging artwork are outside the
required EP3 public demo.

If an external asset is later used, provenance/license metadata must be
explicit.

---

# 12. Determinism

SKU metadata itself must not depend on a random seed.

Randomness belongs to:

```text
scene population
placement
camera
lighting
artifact generation
```

A given `sku_id` always resolves to the same frozen product metadata
within a SKU pack version.

---

# 13. Validation Rules

A valid SKU must satisfy:

```text
schema_version == bvt-sku-1
sku_id is unique
class_id >= 0
class_name is non-empty
width_m > 0
depth_m > 0
height_m > 0
package_type is supported
geometry_template is supported
base_color contains 4 values
base_color values are within 0..1
```

---

# 14. Versioning

SKU metadata contract:

```text
bvt-sku-1
```

Breaking changes require:

```text
bvt-sku-2
```

Changing only SKU pack contents does not require a schema version
change.

---

# 15. Out of Scope

Not part of SKU v0.1:

```text
real GTIN integration
commercial brand databases
nutrition metadata
pricing
inventory quantities
planogram compliance rules
OCR label metadata
multi-language commercial catalogs
```

These may be layered on later without changing the core synthetic SKU
identity model.
