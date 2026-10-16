import json
import pytest
from travel_ai.local import compatibility, load_catalog, install_model


def test_compatibility():
    model = {"min_ram_gb": 8, "download_size_gb": 2}
    result = compatibility(model, {"ram_gb": 4, "disk_free_gb": 20,
                                   "os": "Linux", "architecture": "x86_64"})
    assert not result["eligible"]
    assert "Insufficient total RAM" in result["warnings"]


def test_unapproved_model_cannot_download(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text(json.dumps({"models": {"test": {"status": "candidate"}}}))
    with pytest.raises(ValueError, match="approval"):
        install_model("test", catalog, tmp_path)


def test_catalog_read(tmp_path):
    catalog = tmp_path / "catalog.json"
    catalog.write_text('{"models":{"a":{"status":"candidate"}}}')
    assert "a" in load_catalog(catalog)
