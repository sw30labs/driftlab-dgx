"""Registry paths resolve relative to the registry file's directory."""

from pathlib import Path

from driftlab.monitor.registry import load_registry


def test_registry_relative_paths_resolve_against_registry_dir(tmp_path):
    estate = tmp_path / "estate"
    (estate / "baselines").mkdir(parents=True)
    (estate / "traces").mkdir()
    (estate / "baselines" / "b.json").write_text("{}")
    (estate / "traces" / "t.jsonl").write_text("{}\n")
    registry = estate / "agents.yaml"
    registry.write_text(
        "agents:\n"
        "  - id: demo\n"
        "    baseline: baselines/b.json\n"
        "    trace: traces/t.jsonl\n"
        "  - id: absolute\n"
        "    baseline: /etc/hostname\n"
        "    trace: /etc/hostname\n"
    )
    specs = {a.id: a for a in load_registry(registry)}
    assert specs["demo"].baseline == str((estate / "baselines" / "b.json").resolve())
    assert specs["demo"].trace == str((estate / "traces" / "t.jsonl").resolve())
    assert specs["absolute"].baseline == "/etc/hostname"


def test_seed_registry_paths_resolve_to_existing_files():
    seed = Path(__file__).resolve().parent.parent / "src" / "driftlab" / "seed"
    specs = load_registry(seed / "agents.yaml")
    assert specs, "seed registry must not be empty"
    for a in specs:
        assert Path(a.baseline).is_file(), a.baseline
        assert Path(a.trace).is_file(), a.trace
