# Changelog

All notable public changes to Blender Visual Toolkit are documented
here.

## 0.1.0 — 2026-11-02

### Added

- Blender add-on project workflow.
- Deterministic dataset generation.
- YOLO bounding-box annotation.
- Placement, camera and lighting randomization.
- Artifact Engine v1 with eleven providers.
- Retail edge cases:
  - Wrong Angle;
  - Wrong Position;
  - Empty Slot;
  - Occlusion.
- Productized dataset layout.
- Generation configuration snapshot.
- Train / validation / test splits.
- Dataset statistics.
- Dataset health report.
- Dataset validation.
- SHA-256 integrity manifest.
- Deterministic dataset ZIP.
- Structured CLI error contract.
- Blender UI `Generate Dataset` workflow.
- Frozen Beverage Fridge Retail Demo.
- Eight synthetic SKU classes.
- Public `clean`, `balanced`, `artifacts` and `stress` presets.
- Public sample dataset.
- Public showcase outputs.
- Demo video.
- Retail Demo licensing and attribution records.

### Changed

- Public v0.1 support baseline is Blender 5.2 LTS.
- Dataset manifest advanced to the v0.1 productized contract.

### Fixed

- Retail refrigerator glass behavior for dataset rendering.
- Dataset productization smoke expectations after manifest schema
  versioning.
- Quick Start acceptance now follows the real `Initialize Project`
  UI step.

### Deprecated

None.

### Removed

None.

### Security

No known release-specific security fix is required for v0.1.0.

### Known Issues

- Only Blender 5.2 LTS on Windows is part of the v0.1 acceptance
  matrix.
- COCO and segmentation exports are outside the v0.1 release scope.
- Distributed/cloud rendering is not included.
- Training and sim-to-real benchmarking belong to the next research
  milestone.
