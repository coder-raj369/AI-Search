from pathlib import Path

from localsearch.config import LocalSearchConfig
from localsearch.scanner.discovery import scan_paths


def test_default_config_has_supported_extensions():
    config = LocalSearchConfig()

    assert ".py" in config.supported_extensions
    assert ".ipynb" in config.supported_extensions
    assert ".txt" in config.supported_extensions


def test_scan_paths_returns_supported_files(tmp_path):
    root = tmp_path / "docs"
    nested = root / "nested"
    nested.mkdir(parents=True)

    (root / "a.py").write_text("print('hello')\n", encoding="utf-8")
    (nested / "b.md").write_text("# Hello\n", encoding="utf-8")
    (nested / "skip.bin").write_bytes(b"\x00\x01\x02\x03")

    config = LocalSearchConfig()
    files = scan_paths([str(root)], config=config)

    paths = {f.path for f in files}
    assert str(root / "a.py") in paths
    assert str(nested / "b.md") in paths
    assert str(nested / "skip.bin") not in paths


def test_scan_paths_skips_ignored_directories_and_symlinks(tmp_path):
    root = tmp_path / "docs"
    root.mkdir()
    (root / ".git").mkdir()
    (root / ".git" / "ignored.py").write_text("print('x')\n", encoding="utf-8")
    (root / "keep.py").write_text("print('keep')\n", encoding="utf-8")

    real_file = root / "real.txt"
    real_file.write_text("hello", encoding="utf-8")
    link_path = root / "link.txt"
    try:
        link_path.symlink_to(real_file)
    except OSError:
        link_path = None

    config = LocalSearchConfig()
    files = scan_paths([str(root)], config=config)
    paths = {f.path for f in files}

    assert str(root / "keep.py") in paths
    assert str(root / "real.txt") in paths
    assert str(root / ".git" / "ignored.py") not in paths
    if link_path is not None:
        assert str(link_path) not in paths
