import json
from pathlib import Path


ROOT = Path(
    __file__
).resolve().parents[1]


environment = json.loads(
    (
        ROOT
        / "benchmarks"
        / "environment-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


protocol = json.loads(
    (
        ROOT
        / "benchmarks"
        / "protocol-v0.1.json"
    ).read_text(
        encoding="utf-8"
    )
)


torch_data = environment[
    "torch"
]


assert (
    torch_data[
        "cuda_available"
    ]
    is True
)


assert (
    torch_data[
        "version"
    ].startswith(
        "2.15.0+cu132"
    )
)


assert (
    torch_data[
        "torchvision_version"
    ].startswith(
        "0.29.2+cu132"
    )
)


assert (
    environment[
        "training_device"
    ]
    == "cuda:0"
)


assert (
    environment[
        "gpu"
    ][
        "name"
    ]
    == "NVIDIA GeForce RTX 3050"
)


assert (
    environment[
        "gpu"
    ][
        "memory_bytes"
    ]
    > 7_000_000_000
)


baseline = protocol[
    "baseline"
]


assert (
    baseline[
        "training_device"
    ]
    == "cuda:0"
)


assert (
    baseline[
        "gpu_required"
    ]
    is True
)


assert (
    baseline[
        "cuda_wheel"
    ]
    == "cu132"
)


print(
    "benchmark_cuda_available=True"
)

print(
    "benchmark_cuda_wheel=cu132"
)

print(
    "benchmark_training_device=cuda:0"
)

print(
    "benchmark_gpu="
    + environment[
        "gpu"
    ][
        "name"
    ]
)

print(
    "BVT_BENCHMARK_GPU_ENVIRONMENT=OK"
)

print(
    "RESULT=PASS"
)
