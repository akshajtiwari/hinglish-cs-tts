#!/usr/bin/env python3
"""Print the torch and CUDA versions and the GPUs, and check that f5_tts imports (called by server_setup.sh)."""
import torch
import f5_tts  # noqa: F401  (only checks that the install worked)

print("torch", torch.__version__, "cuda", torch.version.cuda, "gpus", torch.cuda.device_count())
for i in range(torch.cuda.device_count()):
    gpu = torch.cuda.get_device_properties(i)
    print(f"  {i}: {gpu.name} {gpu.total_memory / 2**30:.1f} GiB sm_{gpu.major}{gpu.minor}")
print("bf16 supported:", torch.cuda.is_bf16_supported())
