# BVT Retail Demo v0.1 — Known Limitations

Version: 0.1

Retail Demo v0.1 is intentionally narrow.

It demonstrates one complete, reproducible retail dataset workflow
rather than attempting to implement the entire long-term BVT roadmap.

## Reference scene

v0.1 freezes one canonical public scene:

```text
Beverage Fridge
```

Additional retail environments are outside the EP6 release scope.

## SKU pack

The reference demo contains eight synthetic SKU classes.

The demo does not ship real commercial product identities or branded
packaging.

## Annotation format

The implemented public v0.1 demo focuses on YOLO object-detection
labels and bounding boxes.

COCO export, segmentation masks, depth maps, normal maps and keypoints
are not part of the frozen Retail Demo v0.1 release contract.

## Artifact Engine

Artifact Engine v1 is frozen at eleven providers.

Retail Demo v0.1 does not add new artifact types.

## Retail edge cases

The structural retail scenarios frozen for v0.1 are:

```text
Wrong Angle
Wrong Position
Empty Slot
Occlusion
```

They are scene mutations and are separate from Artifact Engine.

## Resolution

The current public generation workflow uses the v0.1 render contract
and UI exposed by BVT.

Retail Demo v0.1 is not intended to be a general render-management
suite.

## Blender acceptance matrix

The v0.1 release is accepted against Blender 5.2 LTS.

Behavior on Blender versions outside the release acceptance matrix is
not guaranteed by EP6.

## Performance

Generation runs locally through Blender.

Render time depends on scene complexity, hardware and selected frame
count.

v0.1 does not provide distributed, cloud or server rendering.

## Training and benchmark

Retail Demo v0.1 generates datasets.

It does not train YOLO models and does not claim sim-to-real
performance improvements.

Training benchmarks and sim-to-real research belong to EP7.

## Assets

The frozen reference SKU identities are synthetic.

The frozen BVT Retail Demo assets and the public sample dataset are
licensed under CC BY 4.0.

See `LICENSES.md`, `ATTRIBUTIONS.md` and
`SAMPLE_DATASET_LICENSE.md`.

## API stability

The v0.1 contracts are intentionally versioned, but the overall
project is still an early public release.

Future versions may extend schemas through explicit versioned
contracts.
