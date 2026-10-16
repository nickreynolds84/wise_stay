"""Approved-model registry, compatibility checks, safe download and inference."""
import hashlib
import json
import os
import platform
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen


def load_catalog(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "models" not in data:
        raise ValueError("Catalog must contain a models mapping")
    return data["models"]


def system_info():
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024 ** 3)
    except ImportError:
        ram_gb = None
    return {"os": platform.system(), "architecture": platform.machine(),
            "ram_gb": ram_gb, "disk_free_gb": shutil.disk_usage(Path.home()).free / (1024 ** 3)}


def compatibility(model, system=None):
    system = system or system_info()
    warnings = []
    if system["ram_gb"] is None:
        warnings.append("RAM unknown: install psutil to enable memory checks")
    elif system["ram_gb"] < model["min_ram_gb"]:
        warnings.append("Insufficient total RAM")
    if system["disk_free_gb"] < model["download_size_gb"] * 1.25:
        warnings.append("Insufficient free disk space, including download headroom")
    if model.get("supported_os") and system["os"] not in model["supported_os"]:
        warnings.append("Unsupported operating system")
    if model.get("supported_arch") and system["architecture"] not in model["supported_arch"]:
        warnings.append("Unsupported CPU architecture")
    return {"eligible": not warnings, "warnings": warnings, "system": system}


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def install_model(model_id, catalog_path, model_dir=None):
    catalog = load_catalog(catalog_path)
    if model_id not in catalog:
        raise ValueError("Model is not in the approved catalog")
    model = catalog[model_id]
    if model.get("status") != "approved":
        raise ValueError("Model has not passed approval tests")
    expected = model["sha256"].lower()
    if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
        raise ValueError("Invalid SHA-256 digest in catalog")
    url = model["download_url"]
    if urlparse(url).scheme != "https":
        raise ValueError("Model download must use HTTPS")
    folder = Path(model_dir or Path.home() / ".travel_ai" / "models")
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / (model_id + ".gguf")
    if target.exists() and _sha256(target) == expected:
        return target
    check = compatibility(model)
    if not check["eligible"]:
        raise RuntimeError("Compatibility check failed: " + "; ".join(check["warnings"]))
    fd, temp_name = tempfile.mkstemp(prefix="model-", suffix=".part", dir=folder)
    os.close(fd)
    temp = Path(temp_name)
    try:
        # Download to a temporary file, never directly to the final model path.
        with urlopen(url, timeout=60) as response, open(temp, "wb") as output:
            if urlparse(response.geturl()).scheme != "https":
                raise RuntimeError("Download redirected to a non-HTTPS URL")
            shutil.copyfileobj(response, output, length=1024 * 1024)
        if _sha256(temp) != expected:
            raise RuntimeError("Downloaded model failed SHA-256 verification")
        temp.replace(target)
        return target
    finally:
        temp.unlink(missing_ok=True)


class LocalAI:
    def __init__(self, model_path, context_size=4096, gpu_layers=0):
        from llama_cpp import Llama  # Optional dependency, only loaded for inference.
        self.engine = Llama(model_path=str(model_path), n_ctx=context_size,
                           n_gpu_layers=gpu_layers, verbose=False)

    def generate_json(self, system_prompt, user_prompt, max_tokens=700):
        result = self.engine.create_chat_completion(
            messages=[{"role": "system", "content": system_prompt},
                      {"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"},
            temperature=0.1, max_tokens=max_tokens)
        content = result["choices"][0]["message"]["content"]
        if not content:
            raise ValueError("Model returned empty content")
        return json.loads(content)
