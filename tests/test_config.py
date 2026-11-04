from engine.config import TOKEN_ENV, load_config, save_token


def test_local_overrides_and_env_wins(tmp_path, monkeypatch):
    (tmp_path / "config.yaml").write_text(
        "default_lang: en\nudemy:\n  base_url: https://www.udemy.com\n  max_concurrency: 4\n", encoding="utf-8"
    )
    monkeypatch.delenv(TOKEN_ENV, raising=False)
    assert "access_token" not in load_config(tmp_path)["udemy"]

    save_token("file-token", tmp_path)
    cfg = load_config(tmp_path)
    assert cfg["udemy"] == {"base_url": "https://www.udemy.com", "max_concurrency": 4, "access_token": "file-token"}

    monkeypatch.setenv(TOKEN_ENV, "env-token")
    assert load_config(tmp_path)["udemy"]["access_token"] == "env-token"


def test_save_token_keeps_other_keys(tmp_path):
    (tmp_path / "config.local.yaml").write_text("udemy:\n  base_url: https://acme.udemy.com\n", encoding="utf-8")
    save_token("t1", tmp_path)
    save_token("t2", tmp_path)
    cfg = load_config(tmp_path)
    assert cfg["udemy"]["base_url"] == "https://acme.udemy.com"
    assert cfg["udemy"]["access_token"] == "t2"
