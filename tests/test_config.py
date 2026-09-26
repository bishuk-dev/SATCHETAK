import os

from satchetak.config import _load_env_file


def test_env_file_loads_values_without_overriding_process_environment(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# local settings\nCDSE_CLIENT_ID=from-file\nQWEN_MODEL='qwen2.5:1.5b'\nexport PLANETARY_COMPUTER_ENABLED=false\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("CDSE_CLIENT_ID", raising=False)
    monkeypatch.delenv("QWEN_MODEL", raising=False)
    monkeypatch.setenv("PLANETARY_COMPUTER_ENABLED", "true")

    _load_env_file(env_file)

    assert os.environ["CDSE_CLIENT_ID"] == "from-file"
    assert os.environ["QWEN_MODEL"] == "qwen2.5:1.5b"
    assert os.environ["PLANETARY_COMPUTER_ENABLED"] == "true"
