import subprocess
import platform
import shutil
from typing import Dict, Any

def detect_hardware() -> Dict[str, Any]:
    """Detects local GPU and memory resources with cross-platform fallback."""
    # 1. Check NVIDIA GPU via nvidia-smi
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        try:
            # Query GPU name and total memory in MB
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=gpu_name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                check=True
            )
            line = result.stdout.strip().split("\n")[0]
            parts = line.split(",")
            if len(parts) == 2:
                gpu_name = parts[0].strip()
                vram_mb = int(parts[1].strip())
                return {
                    "gpu_name": gpu_name,
                    "vram_mb": vram_mb,
                    "platform": "nvidia_cuda"
                }
        except Exception:
            pass

    # 2. Check Apple Silicon (macOS)
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        try:
            sysctl_res = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True)
            chip_name = sysctl_res.stdout.strip() or "Apple Silicon"
            # Get total RAM
            mem_res = subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True)
            total_bytes = int(mem_res.stdout.strip())
            vram_mb = int(total_bytes / (1024 * 1024))
            return {
                "gpu_name": f"{chip_name} (Unified Memory)",
                "vram_mb": vram_mb,
                "platform": "apple_metal"
            }
        except Exception:
            pass

    # 3. CPU Fallback
    import os
    cpu_count = os.cpu_count() or 4
    return {
        "gpu_name": f"CPU Node ({cpu_count} cores, {platform.machine()})",
        "vram_mb": 8192,
        "platform": "cpu"
    }
