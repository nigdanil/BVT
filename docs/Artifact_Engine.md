# Blender Visual Toolkit

## Artifact Engine

Version: 1.0 Frozen
Engine version: `artifact-engine-v1`

---

# Цель документа

Artifact Engine — центральный модуль Blender Visual Toolkit для
детерминированного моделирования реальных дефектов и условий съёмки.

Его задача — сокращать Domain Gap между синтетическими и реальными
изображениями.

Artifact Engine не создаёт эффекты «ради красоты».

Он моделирует условия, которые реально влияют на Computer Vision:

- пересвет;
- отражения;
- отпечатки;
- запотевание;
- иней;
- пыль;
- капли воды;
- царапины;
- motion blur;
- sensor noise;
- compression artifacts.

---

# Архитектурная граница

Artifact Engine отвечает за артефакты изображения и материала.

Он не отвечает за:

```text
placement объектов
wrong position
wrong angle
empty slot
occlusion topology
SKU generation
dataset split
model training
```

Эти задачи принадлежат другим слоям BVT.

Основной pipeline:

```text
Project
↓
Scene
↓
Assets
↓
Placement
↓
Camera
↓
Lighting
↓
Domain Randomization
↓
Artifact Engine
↓
Render
↓
Annotation
↓
Validation
↓
Export
```

---

# Artifact Engine v1

Версия движка:

```text
artifact-engine-v1
```

В v1 зафиксировано ровно:

```text
11 providers
```

После EP2 новые artifact types замораживаются до Retail Demo v0.1.

---

# Providers v1

## Pre-render

| Order | Artifact | Category |
|---:|---|---|
| 100 | `over_exposure` | lighting |
| 100 | `reflection` | glass |
| 110 | `fingerprints` | glass |
| 120 | `condensation` | glass |
| 130 | `frost` | glass |
| 140 | `dust` | glass |
| 150 | `water_drops` | glass |
| 160 | `scratches` | glass |

## Post-render

| Order | Artifact | Category |
|---:|---|---|
| 50 | `motion_blur` | camera |
| 100 | `noise` | sensor |
| 200 | `jpeg_compression` | compression |

---

# Canonical execution order

Сортировка:

```text
stage
execution_order
artifact_id
```

Итоговый порядок manifest records:

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

`over_exposure` и `reflection` имеют order `100`.

Их порядок стабилизируется третьим ключом:

```text
artifact_id
```

поэтому:

```text
over_exposure
→ reflection
```

---

# Generic controls

Базовая публичная модель каждого artifact:

```text
Enabled
Probability
Intensity
```

Диапазоны:

```text
0 <= Probability <= 1
0 <= Intensity <= 1
```

Некоторые существующие v1 providers имеют дополнительные параметры.

Например:

```text
Reflection:
    min_roughness

Fingerprints:
    count
    transparency
    size

Motion Blur:
    direction range
    max length

JPEG Compression:
    quality
    chroma loss
```

Добавление новых generic controls требует новой версии контракта.

---

# Provider API

Базовый контракт:

```text
ArtifactProvider
```

Identity:

```text
artifact_id
category
description
stage
execution_order
```

Lifecycle/API:

```text
validate_config(config)

capture(scene)

apply(
    scene,
    context,
    baseline,
)

apply_post_render(
    scene,
    image_path,
    context,
    baseline,
)

reset(
    scene,
    baseline,
)

preview(
    scene,
    context,
    baseline,
)

compatibility_rules()

manifest_export(
    context,
    applied,
    metadata=None,
)
```

---

# ArtifactConfig

Resolved configuration:

```text
artifact_id
enabled
probability
intensity
options
```

---

# ArtifactContext

Per-frame context:

```text
config
frame_seed
artifact_seed
decision_roll
```

---

# Lifecycle

Перед генерацией BVT захватывает baseline каждого provider.

Перед каждым кадром:

```text
restore_artifacts()
```

возвращает сцену к baseline.

После этого:

```text
pre-render artifacts
→ Blender render
→ post-render artifacts
→ manifest
```

Reset выполняется в обратном registration order.

Это защищает цепочки вложенных изменений.

---

# Glass chain

Основная v1-цепочка:

```text
Reflection
→ Fingerprints
→ Condensation
→ Frost
→ Dust
→ Water Drops
→ Scratches
```

Target:

```text
material role = GLASS
```

Используемые shader targets:

```text
BSDF_PRINCIPLED
BSDF_GLASS
```

Основная связанная цепочка строится через Roughness.

---

# Glass input progression

```text
Fingerprints:
    clean

Condensation:
    clean
    fingerprints

Frost:
    clean
    fingerprints
    condensation

Dust:
    clean
    fingerprints
    condensation
    frost

Water Drops:
    clean
    fingerprints
    condensation
    frost
    dust

Scratches:
    clean
    fingerprints
    condensation
    frost
    dust
    water_drops
```

Reflection изменяет effective Roughness до linked-chain и поэтому не
требует отдельного `input_mode`.

Подробная frozen-матрица:

```text
docs/contracts/Artifact-Engine-v1-Compatibility-Matrix.md
```

---

# Reset Glass chain

Обратный порядок:

```text
Scratches
→ Water Drops
→ Dust
→ Frost
→ Condensation
→ Fingerprints
→ Reflection
→ original material state
```

Temporary BVT nodes/images должны удаляться.

User-owned shader state не должен повреждаться в тех providers, где
compatibility contract заявляет preservation.

---

# Post-render chain

После Blender render:

```text
Motion Blur
→ Noise
→ JPEG Compression
```

JPEG provider моделирует compression через внутренний JPEG
encode/decode.

Но финальный dataset contract остаётся:

```text
PNG
```

---

# Deterministic seeding

Frame strategy:

```text
FRAME_SEED_STRATEGY = sha256-v1
```

Frame seed:

```text
derive_frame_seed(
    project_seed,
    frame_index,
)
```

Subseed strategy:

```text
SUBSEED_STRATEGY = sha256-namespace-v1
```

Artifact seed:

```text
derive_subseed(
    frame_seed,
    "artifact",
    artifact_id,
)
```

Decision roll:

```text
random.Random(
    artifact_seed
).random()
```

Artifact применяется, когда:

```text
enabled
and decision_roll < probability
```

Каждый provider получает независимый namespace.

Изменение количества RNG-вызовов одного provider не должно менять
randomness другого provider.

---

# Manifest

Canonical artifact record содержит 17 полей:

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

Provider-specific metadata хранится внутри:

```text
parameters
```

Artifact seed хранится только в:

```text
record["seed"]
```

---

# Artifact Engine wrapper

На каждый frame:

```text
enabled
version
artifacts
```

Если Engine выключен:

```text
enabled   = false
version   = artifact-engine-v1
artifacts = []
```

---

# Reproducibility

Canonical repeat-run contract:

```text
same seed
+ same config
+ same scene
+ same BVT/Blender environment
→ same manifest
→ same labels
→ same decoded image pixels
```

Для canonical acceptance требуется:

```text
manifest bytes identical
label bytes identical
decoded RGBA pixels identical
RMSE = 0
max error = 0
```

SHA256 PNG-файла не является контрактом воспроизводимости.

Blender может записывать различающийся PNG container metadata при
полностью одинаковом decoded image content.

---

# Canonical acceptance

Конфигурация:

```text
configs/artifact-engine-v1-acceptance.json
```

В ней одновременно включены все 11 providers:

```text
Probability = 1
fixed placement
fixed camera
fixed lighting
GLASS material
```

Acceptance проверяет:

```text
11 providers per frame
canonical order
all providers applied
provider categories
stage/order
17 manifest fields
artifact seeds
decision rolls
Glass input chain
post-render chain
repeat manifest equality
repeat label equality
decoded pixel equality
multiple deterministic frame variants
PNG output
validation PASS
```

Audit:

```text
tools/artifact_engine_v1_acceptance_audit.py
```

---

# Regression baseline

На момент v1 Freeze:

```text
TOTAL=27
PASS=27
FAIL=0
```

Regression suite является обязательным release gate.

---

# Freeze policy

После Artifact Engine v1 Freeze разрешены:

```text
bug fixes
performance improvements
test improvements
documentation improvements
behavior-preserving refactors
```

Без explicit contract revision запрещены:

```text
новый provider
удаление provider
rename artifact_id
смена category
смена stage
смена execution_order
смена seed strategy
смена decision algorithm
удаление/rename manifest fields
изменение lifecycle semantics
изменение compatibility semantics
```

Новые artifact types отложены до Retail Demo v0.1.

---

# Что не входит в Artifact Engine v1

Следующие идеи остаются будущими:

```text
Rolling Shutter
Lens Distortion
Chromatic Aberration
Defocus
Under Exposure
Hard Shadows
Color Shift
Mixed Lighting
Dirty Glass
Damaged Package
Missing Label
Torn Label
Wet Surface
Human Reflection
Foreign Object
```

Product/scene state changes вроде:

```text
Wrong Angle
Wrong Position
Empty Slot
Occlusion
```

не должны автоматически становиться Artifact Engine providers.

Их architecture boundary фиксируется отдельно в EP4.

---

# Связанные документы

```text
docs/contracts/Artifact-Engine-v1-Freeze.md
docs/contracts/Artifact-Engine-v1-Compatibility-Matrix.md
configs/artifact-engine-v1-acceptance.json
tools/artifact_engine_v1_acceptance_audit.py
docs/Backlog.md
docs/Roadmap.md
```

---

# Статус

```text
Artifact Engine v1 = Frozen
```

Freeze acceptance:

```text
regression PASS
canonical acceptance PASS
package PASS
clean Blender profile install PASS
```

Artifact Engine v1 frozen.

New artifact providers are not accepted before Retail Demo v0.1
without an explicit contract revision.
