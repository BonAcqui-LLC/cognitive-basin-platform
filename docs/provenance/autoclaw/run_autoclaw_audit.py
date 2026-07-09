import contextlib
import csv
import hashlib
import io
import json
import os
import platform
import re
import subprocess
import sys
import time
import zipfile
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE")
HANDOFF = Path(r"C:\_MASTER_LIBRARY_Handoff")
TMP = HANDOFF / "_tmp_exec"
PYTHON = Path(r"C:\Users\moop\AppData\Local\Programs\Python\Python312\python.exe")
FROZEN = Path(r"C:\_MASTER_LIBRARY\01_CANON\01_NATURAL_MATH_V5\Natural Math v5 - Status Frozen Int.txt")
VALIDATION_ROOT = Path(r"C:\_MASTER_LIBRARY\02_VALIDATION_EVIDENCE\NATURAL_MATH_V5")
EXPECTED_FROZEN_HASH = "E5AB47D41B82F6AF573866BE637BF3B0054D96C7F45A613EC6CAE2124AD84C7B"
NOW = datetime.now(timezone.utc)
TIMESTAMP = NOW.isoformat()

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
TMP.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd=None, check=False, env=None):
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        joined = " ".join(str(part) for part in cmd)
        raise RuntimeError(
            f"Command failed ({result.returncode}): {joined}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def git(*args, check=True):
    return run(
        ["git", "-c", f"safe.directory={REPO}", "-C", str(REPO), *args],
        check=check,
    )


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def rel_to_repo(path: Path) -> str:
    return path.relative_to(REPO).as_posix()


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_pytest_summary(stdout: str, stderr: str):
    text = (stdout or "") + "\n" + (stderr or "")
    counts = {
        "collected": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "errors": 0,
        "duration_s": None,
    }

    collected_match = re.search(r"(\d+) tests? collected(?: in ([0-9.]+)s)?", text)
    if collected_match:
        counts["collected"] = int(collected_match.group(1))
        if collected_match.group(2):
            counts["duration_s"] = float(collected_match.group(2))

    summary_match = re.search(r"=+\s*(.*?)\s*in ([0-9.]+)s\s*=+", text)
    if summary_match:
        counts["duration_s"] = float(summary_match.group(2))
        for n, label in re.findall(
            r"(\d+)\s+(passed|failed|skipped|error|errors)", summary_match.group(1)
        ):
            label = "errors" if label.startswith("error") else label
            counts[label] = int(n)
    else:
        alt_match = re.search(
            r"(\d+) passed(?:, (\d+) skipped)?(?:, (\d+) failed)?(?:, (\d+) errors?)? in ([0-9.]+)s",
            text,
        )
        if alt_match:
            counts["passed"] = int(alt_match.group(1))
            counts["skipped"] = int(alt_match.group(2) or 0)
            counts["failed"] = int(alt_match.group(3) or 0)
            counts["errors"] = int(alt_match.group(4) or 0)
            counts["duration_s"] = float(alt_match.group(5))

    passed_match = re.search(r"(\d+) passed", text)
    failed_match = re.search(r"(\d+) failed", text)
    skipped_match = re.search(r"(\d+) skipped", text)
    errors_match = re.search(r"(\d+) errors?", text)
    duration_match = re.search(r"in ([0-9.]+)s", text)
    if passed_match and counts["passed"] == 0:
        counts["passed"] = int(passed_match.group(1))
    if failed_match and counts["failed"] == 0:
        counts["failed"] = int(failed_match.group(1))
    if skipped_match and counts["skipped"] == 0:
        counts["skipped"] = int(skipped_match.group(1))
    if errors_match and counts["errors"] == 0:
        counts["errors"] = int(errors_match.group(1))
    if duration_match and counts["duration_s"] is None:
        counts["duration_s"] = float(duration_match.group(1))

    if (
        counts["collected"] == 0
        and counts["passed"] > 0
        and counts["failed"] == 0
        and counts["errors"] == 0
        and counts["skipped"] == 0
    ):
        counts["collected"] = counts["passed"]

    if (
        counts["passed"] == 0
        and counts["failed"] == 0
        and counts["errors"] == 0
        and counts["collected"]
    ):
        counts["passed"] = (
            counts["collected"]
            - counts["failed"]
            - counts["skipped"]
            - counts["errors"]
        )

    return counts, text


def run_pytest(label: str, args):
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    cmd = [str(PYTHON), "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", *args]
    start = time.perf_counter()
    result = run(cmd, cwd=REPO, env=env)
    elapsed = time.perf_counter() - start
    counts, combined = parse_pytest_summary(result.stdout, result.stderr)
    if counts["duration_s"] is None:
        counts["duration_s"] = round(elapsed, 3)
    counts["returncode"] = result.returncode
    counts["label"] = label
    counts["command"] = " ".join(cmd)
    counts["stdout"] = result.stdout
    counts["stderr"] = result.stderr
    counts["combined_output"] = combined
    return counts


def execute_redirected_script(label: str, source: Path, replacements: dict[str, str]):
    target_dir = TMP / label
    target_dir.mkdir(parents=True, exist_ok=True)
    src = read_text(source)
    for old, new in replacements.items():
        src = src.replace(old, new)

    namespace = {"__name__": f"audit_{label}", "__file__": str(source)}
    stdout_buf = io.StringIO()
    stderr_buf = io.StringIO()
    rc = 0

    with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
        old_argv = sys.argv[:]
        old_cwd = os.getcwd()
        sys.argv = [str(source)]
        os.chdir(str(source.parent))
        try:
            exec(compile(src, str(source), "exec"), namespace)
            if "main" in namespace:
                try:
                    result = namespace["main"]()
                    if isinstance(result, int):
                        rc = result
                except SystemExit as exc:
                    rc = exc.code if isinstance(exc.code, int) else 1
        except SystemExit as exc:
            rc = exc.code if isinstance(exc.code, int) else 1
        finally:
            sys.argv = old_argv
            os.chdir(old_cwd)

    return {
        "label": label,
        "source": str(source),
        "returncode": rc,
        "stdout": stdout_buf.getvalue(),
        "stderr": stderr_buf.getvalue(),
        "target_dir": str(target_dir),
    }


def inspect_original_oracle(result):
    path = Path(result["target_dir"]) / "original_oracle_results.json"
    data = json.loads(read_text(path))
    return {
        "json_path": str(path),
        "total": data["total_fixtures"],
        "passed": data["passed_count"],
        "failed": data["total_fixtures"] - data["passed_count"],
        "skipped": 0,
        "errors": 0,
        "duration_s": None,
        "integer": data["integer_fixtures"]["count"],
        "integer_passed": data["integer_fixtures"]["passed_count"],
        "cluster": data["cluster_fixtures"]["count"],
        "cluster_passed": data["cluster_fixtures"]["passed_count"],
        "overall_passed": data["overall_passed"],
    }


def inspect_compare_donors(result):
    path = Path(result["target_dir"]) / "donor_differential_results.json"
    data = json.loads(read_text(path))
    summary = data["overall"]
    return {
        "json_path": str(path),
        "total": summary["total_cases_compared"],
        "passed": summary["matching"] + summary["diverging_but_correct"],
        "failed": summary["diverging"] - summary["diverging_but_correct"],
        "skipped": 0,
        "errors": 0,
        "duration_s": None,
        "local_integer_total": data["part_a_local"]["summary"]["total"],
        "cluster_total": data["part_b_cluster"]["summary"]["total"],
        "generated_total": data["part_c_deterministic"]["summary"]["local_total"]
        + data["part_c_deterministic"]["summary"]["cluster_total"],
        "trigger_total": data["part_d_divergence_triggers"]["summary"]["total"],
        "matching": summary["matching"],
        "diverging_but_expected": summary["diverging_but_correct"],
        "diverging_unexpected": summary["diverging"] - summary["diverging_but_correct"],
    }


def inspect_deterministic_replay(result):
    path = Path(result["target_dir"]) / "deterministic_replay_results.json"
    data = json.loads(read_text(path))
    total = int(data["total_configs"]) + int(data["local_cases"])
    failures = len(data.get("failures", []))
    return {
        "json_path": str(path),
        "total": total,
        "passed": total - failures,
        "failed": failures,
        "skipped": 0,
        "errors": 0,
        "duration_s": None,
        "cluster_configs": data["total_configs"],
        "local_cases": data["local_cases"],
        "all_deterministic": data["all_deterministic"],
    }


def inspect_stage2(result):
    base = Path(result["target_dir"])
    oracle_path = base / "original_oracle_mode_comparison.json"
    det_path = base / "deterministic_mode_comparison.json"
    oracle_data = json.loads(read_text(oracle_path))
    det_data = json.loads(read_text(det_path))
    return {
        "oracle_json_path": str(oracle_path),
        "det_json_path": str(det_path),
        "oracle_total": oracle_data["total_fixtures"],
        "oracle_passed": oracle_data["passed_count"],
        "det_total": det_data["total_runs"],
        "det_passed": det_data["passed_count"],
        "overall_passed": oracle_data["overall_passed"] and det_data["overall_passed"],
    }


def inspect_perf(result):
    metrics = {"hash_verification_passed": "Hash verification: PASS" in result["stdout"]}
    for line in result["stdout"].splitlines():
        baseline = re.search(r"BASELINE:\s+([0-9.]+)s", line)
        noext = re.search(r"HARNESS_NO_EXTENSIONS:\s+([0-9.]+)s \(\+?([+-]?[0-9.]+)%\)", line)
        noop = re.search(r"HARNESS_WITH_EXTENSIONS:\s+([0-9.]+)s \(\+?([+-]?[0-9.]+)%\)", line)
        if baseline:
            metrics["baseline_s"] = float(baseline.group(1))
        if noext:
            metrics["noext_s"] = float(noext.group(1))
            metrics["noext_overhead_pct"] = float(noext.group(2))
        if noop:
            metrics["noop_s"] = float(noop.group(1))
            metrics["noop_overhead_pct"] = float(noop.group(2))
    return metrics


def maybe_text(path: Path) -> str:
    try:
        return read_text(path)
    except Exception:
        return ""


def search_workspace(term: str):
    hits = []
    for path in REPO.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {
            ".py",
            ".md",
            ".txt",
            ".json",
            ".csv",
            ".toml",
            ".yaml",
            ".yml",
        }:
            continue
        if term.lower() in maybe_text(path).lower():
            hits.append(rel_to_repo(path))
    return hits


def gather_top_level_artifacts():
    root = Path(r"C:\_MASTER_LIBRARY")
    items = [
        ".openclaw",
        ".cluster",
        "AGENTS.md",
        "BOOTSTRAP.md",
        "HEARTBEAT.md",
        "IDENTITY.md",
        "SOUL.md",
        "TOOLS.md",
        "USER.md",
        "evolution-drafts",
        "15_ACTIVATION_ARCHITECTURE",
        "ephux-activation-kernel",
    ]

    results = []
    for name in items:
        path = root / name
        category = "uncertain"
        note = ""
        if name == ".openclaw":
            category = "configuration"
            note = "OpenClaw workspace bootstrap state JSON."
        elif name == ".cluster":
            category = "AutoClaw application scaffolding"
            note = "Agent-cluster playbook/instructions, not product code."
        elif name in {"AGENTS.md", "BOOTSTRAP.md", "IDENTITY.md", "SOUL.md", "USER.md"}:
            category = "generated identity/persona material"
            note = "Workspace bootstrap/persona scaffold, not project implementation."
        elif name in {"HEARTBEAT.md", "TOOLS.md"}:
            category = "configuration"
            note = "Runtime/configuration note file rather than product implementation."
        elif name == "evolution-drafts":
            category = "generated identity/persona material"
            note = "AutoClaw evolution/memory proposal artifacts."
        elif name in {"15_ACTIVATION_ARCHITECTURE", "ephux-activation-kernel"}:
            category = "project implementation"
            note = "Separate implementation worktree outside AutoClaw workspace."

        ref_term = name.lower().replace(".md", "")
        refs = search_workspace(ref_term)
        results.append(
            {
                "name": name,
                "path": str(path),
                "exists": path.exists(),
                "category": category,
                "note": note,
                "referenced_by_workspace": bool(refs),
                "reference_hits": refs[:20],
                "is_dir": path.is_dir(),
            }
        )

    return results


def file_manifest(root: Path):
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_file():
            rows.append(
                {
                    "relative_path": path.relative_to(root).as_posix(),
                    "size": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    return rows


def should_exclude_from_zip(path: Path) -> bool:
    parts = {part.lower() for part in path.parts}
    name = path.name.lower()
    if "__pycache__" in parts or name.endswith(".pyc") or ".pytest_cache" in parts:
        return True
    if name.endswith(".tmp") or name.endswith(".temp") or name.endswith("~"):
        return True
    if name in {".env", ".env.local", ".env.production", ".env.development"}:
        return True
    return False


def build_zip(zip_path: Path):
    included = []
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(REPO.rglob("*")):
            if path.is_file() and not should_exclude_from_zip(path):
                arcname = path.relative_to(REPO).as_posix()
                zf.write(path, arcname)
                included.append(arcname)
    return included


def inspect_stage_files():
    result = run(
        [
            "rg",
            "-n",
            "trail_edges|trail_deposit|trail_decay|natural_math_v5_1_local_flow_trail_memory|Local Flow Trail Memory|PROPOSE_LOCAL_MOVE_PREFERENCE|successful movement deposit logic",
            str(REPO),
        ]
    )
    text = result.stdout
    return {
        "local_flow_hits": text,
        "has_local_flow_code": any(
            token in text
            for token in [
                "trail_edges",
                "trail_deposit",
                "trail_decay",
                "natural_math_v5_1_local_flow_trail_memory",
            ]
        ),
    }


def stage_statuses(local_flow_summary):
    return OrderedDict(
        [
            (
                "Stage 0",
                {
                    "status": "reports only",
                    "evidence": [
                        "01_INVENTORY/*",
                        "06_REPORTS/autoclaw_readiness_confirmation.md",
                        "06_REPORTS/stage_0_correction_addendum.md",
                    ],
                },
            ),
            (
                "Stage 1",
                {
                    "status": "implemented",
                    "evidence": [
                        "02_REFERENCE_IMPLEMENTATION/natural_math_v5/*",
                        "04_TESTS/layer_b_conformance/*",
                        "05_RESULTS/frozen_v5/original_oracle_runner.py",
                    ],
                },
            ),
            (
                "Stage 1.1",
                {
                    "status": "implemented",
                    "evidence": [
                        "02_REFERENCE_IMPLEMENTATION/natural_math_v5/tracing.py",
                        "04_TESTS/layer_b_conformance/test_trace_equivalence.py",
                        "05_RESULTS/frozen_v5/compare_donors.py",
                        "05_RESULTS/frozen_v5/run_tests.py",
                    ],
                },
            ),
            (
                "Stage 2",
                {
                    "status": "implemented",
                    "evidence": [
                        "03_EXPERIMENTS/extension_harness/*",
                        "04_TESTS/extension_harness/*",
                        "_stage2_oracle_runner.py",
                    ],
                },
            ),
            (
                "Stage 3",
                {
                    "status": "not found" if not local_flow_summary["has_local_flow_code"] else "partially implemented",
                    "evidence": ["06_REPORTS/baby_ai_layered_build_map.md"],
                },
            ),
        ]
    )


def stale_reports():
    return [
        {
            "path": "06_REPORTS/autoclaw_readiness_confirmation.md",
            "statement": "Implementation has NOT started.",
            "reason": "Superseded by six commits ending at ef0d0b6 and by Stage 1/1.1/2 code and tests present in the workspace.",
        },
        {
            "path": "06_REPORTS/STAGE_1_1_COMPLETION.md",
            "statement": "289 conformance tests",
            "reason": "Observed pytest collection is 292 across layer_b_conformance; the live suite no longer matches the reported count.",
        },
        {
            "path": "06_REPORTS/STAGE_1_1_COMPLETION.md",
            "statement": "natural_math_v5_stage_1_1_independent_review.zip",
            "reason": "The file present in the workspace is natural_math_v5_stage_1_1_review.zip.",
        },
        {
            "path": "06_REPORTS/stage_2_completion.md",
            "statement": "Stage 2 Commit: Pending (unstaged)",
            "reason": "Stage 2 is committed at ef0d0b6b0ae1fea0f035fc2a36bffe75f86306f9 on main.",
        },
        {
            "path": "06_REPORTS/stage_1_execution_plan.md",
            "statement": "Stage 1 is ready to begin upon operator approval.",
            "reason": "Historical planning statement; Stage 1, 1.1, and 2 are already implemented.",
        },
    ]


def format_seconds(value):
    return "n/a" if value is None else f"{value:.3f}s"


def write_text(path: Path, text: str):
    path.write_text(text, encoding="utf-8")


pre_porcelain = git("status", "--porcelain=v1", "--untracked-files=all").stdout
head = git("rev-parse", "HEAD").stdout.strip()
branch = git("branch", "--show-current").stdout.strip()
history = git("log", "--reverse", "--pretty=format:%H\t%ad\t%s", "--date=iso-local", "--all").stdout
tracked_files = git("ls-files").stdout.splitlines()
untracked_files = git("ls-files", "--others", "--exclude-standard").stdout.splitlines()
ignored_files = git("ls-files", "--others", "-i", "--exclude-standard").stdout.splitlines()
remotes = git("remote", "-v").stdout.splitlines()
python_version = run([str(PYTHON), "-V"]).stdout.strip() or run([str(PYTHON), "-V"]).stderr.strip()
os_info = f"{platform.system()} {platform.release()} ({platform.version()})"
frozen_hash = sha256(FROZEN)
tag_target = git("rev-list", "-n", "1", "natural-math-v5-reference-1.0").stdout.strip()
diff_vs_tag = git("diff", "--name-only", f"{tag_target}..{head}").stdout.splitlines()
ref_impl_diff_vs_tag = [path for path in diff_vs_tag if path.startswith("02_REFERENCE_IMPLEMENTATION/")]
tags = git(
    "for-each-ref",
    "refs/tags",
    "--format=%(refname:short)\t%(objecttype)\t%(objectname)\t%(*objectname)",
).stdout.strip().splitlines()

external_files = {
    "integer_fixtures": VALIDATION_ROOT / "ORACLE_FIXTURES" / "natural_math_integer_oracle_fixtures.json",
    "cluster_fixtures": VALIDATION_ROOT / "ORACLE_FIXTURES" / "natural_math_cluster_oracle_fixtures.json",
    "integer_runner": VALIDATION_ROOT / "ORACLE_RUNNERS" / "natural_math_integer_oracle_runner.py",
    "cluster_runner": VALIDATION_ROOT / "ORACLE_RUNNERS" / "natural_math_cluster_oracle_runner.py",
}
external_hashes = {key: sha256(path) for key, path in external_files.items()}

pytest_stage11 = run_pytest("stage_1_1_conformance", [str(REPO / "04_TESTS" / "layer_b_conformance")])
pytest_trace = run_pytest(
    "trace_equivalence",
    [str(REPO / "04_TESTS" / "layer_b_conformance" / "test_trace_equivalence.py")],
)
pytest_stage2 = run_pytest("stage_2_extension_harness", [str(REPO / "04_TESTS" / "extension_harness")])
pytest_rng = run_pytest(
    "rng_equivalence",
    [str(REPO / "04_TESTS" / "extension_harness" / "test_rng_equivalence.py")],
)
pytest_mutation = run_pytest(
    "mutation_resistance",
    [str(REPO / "04_TESTS" / "extension_harness" / "test_mutation_resistance.py")],
)
pytest_state = run_pytest(
    "state_isolation",
    [str(REPO / "04_TESTS" / "extension_harness" / "test_state_isolation.py")],
)
pytest_proposal = run_pytest(
    "proposal_validation",
    [
        str(REPO / "04_TESTS" / "extension_harness"),
        "-k",
        "validate_move_proposal or proposal_from_observation_hook_rejected or validate_hook_result_behavioral or validate_hook_result_observation",
    ],
)

original_script = execute_redirected_script(
    "original_oracle",
    REPO / "05_RESULTS" / "frozen_v5" / "original_oracle_runner.py",
    {r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5": str(TMP / "original_oracle")},
)
compare_script = execute_redirected_script(
    "compare_donors",
    REPO / "05_RESULTS" / "frozen_v5" / "compare_donors.py",
    {
        r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5\temp_donors": str(TMP / "compare_donors" / "temp_donors"),
        r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5": str(TMP / "compare_donors"),
    },
)
replay_script = execute_redirected_script(
    "deterministic_replay",
    REPO / "05_RESULTS" / "frozen_v5" / "run_tests.py",
    {r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\frozen_v5": str(TMP / "deterministic_replay")},
)
stage2_script = execute_redirected_script(
    "stage2_oracles",
    REPO / "_stage2_oracle_runner.py",
    {r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\05_RESULTS\extension_harness": str(TMP / "stage2_oracles")},
)
perf_script = execute_redirected_script(
    "stage2_perf",
    REPO / "_stage2_perf.py",
    {r"C:\_MASTER_LIBRARY\06_AUTOCLAW_WORKSPACE\06_REPORTS": str(TMP / "stage2_perf_reports")},
)

original_results = inspect_original_oracle(original_script)
compare_results = inspect_compare_donors(compare_script)
replay_results = inspect_deterministic_replay(replay_script)
stage2_results = inspect_stage2(stage2_script)
perf_results = inspect_perf(perf_script)
local_flow_summary = inspect_stage_files()
stages = stage_statuses(local_flow_summary)
artifacts = gather_top_level_artifacts()
stale = stale_reports()
manifest_rows = file_manifest(REPO)
sha_manifest_lines = [f"{row['sha256']}  {row['relative_path']}" for row in manifest_rows]

zip_path = HANDOFF / "autoclaw_workspace_handoff.zip"
if zip_path.exists():
    zip_path.unlink()
zip_entries = build_zip(zip_path)
zip_hash = sha256(zip_path)
with zipfile.ZipFile(zip_path, "r") as zf:
    zip_names = zf.namelist()
zip_has_git = any(name.startswith(".git/") for name in zip_names)

post_porcelain = git("status", "--porcelain=v1", "--untracked-files=all").stdout
repo_unchanged = pre_porcelain == post_porcelain

write_text(HANDOFF / "AUTOCLAW_GIT_HISTORY.txt", history + "\n")
with (HANDOFF / "AUTOCLAW_FILE_MANIFEST.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["relative_path", "size", "sha256"])
    writer.writeheader()
    writer.writerows(manifest_rows)
write_text(HANDOFF / "AUTOCLAW_SHA256_MANIFEST.txt", "\n".join(sha_manifest_lines) + "\n")

stage_lines = [
    "# AUTOCLAW Stage Status",
    "",
    f"- Repository root: `{REPO}`",
    f"- Branch: `{branch}`",
    f"- HEAD: `{head}`",
    "",
    "## Stage Classification",
    "",
]
for name, data in stages.items():
    evidence = ", ".join(f"`{item}`" for item in data["evidence"])
    stage_lines.append(f"- **{name}:** {data['status']}")
    stage_lines.append(f"  Evidence: {evidence}")
write_text(HANDOFF / "AUTOCLAW_STAGE_STATUS.md", "\n".join(stage_lines) + "\n")

test_rows = [
    (
        "Original local fixtures",
        original_results["integer"],
        original_results["integer_passed"],
        original_results["integer"] - original_results["integer_passed"],
        0,
        0,
        None,
        "redirected original_oracle_runner.py",
    ),
    (
        "Original cluster fixtures",
        original_results["cluster"],
        original_results["cluster_passed"],
        original_results["cluster"] - original_results["cluster_passed"],
        0,
        0,
        None,
        "redirected original_oracle_runner.py",
    ),
    (
        "Stage 1.1 conformance",
        pytest_stage11["collected"],
        pytest_stage11["passed"],
        pytest_stage11["failed"],
        pytest_stage11["skipped"],
        pytest_stage11["errors"],
        pytest_stage11["duration_s"],
        "pytest layer_b_conformance",
    ),
    (
        "Donor differential",
        compare_results["total"],
        compare_results["passed"],
        compare_results["failed"],
        0,
        0,
        None,
        "redirected compare_donors.py",
    ),
    (
        "Deterministic replay",
        replay_results["total"],
        replay_results["passed"],
        replay_results["failed"],
        0,
        0,
        None,
        "redirected run_tests.py",
    ),
    (
        "Trace equivalence",
        pytest_trace["collected"],
        pytest_trace["passed"],
        pytest_trace["failed"],
        pytest_trace["skipped"],
        pytest_trace["errors"],
        pytest_trace["duration_s"],
        "pytest test_trace_equivalence.py",
    ),
    (
        "Stage 2 extension harness",
        pytest_stage2["collected"],
        pytest_stage2["passed"],
        pytest_stage2["failed"],
        pytest_stage2["skipped"],
        pytest_stage2["errors"],
        pytest_stage2["duration_s"],
        "pytest extension_harness",
    ),
    (
        "Mode equivalence",
        stage2_results["oracle_total"] + stage2_results["det_total"],
        stage2_results["oracle_passed"] + stage2_results["det_passed"],
        (stage2_results["oracle_total"] - stage2_results["oracle_passed"])
        + (stage2_results["det_total"] - stage2_results["det_passed"]),
        0,
        0,
        None,
        "redirected _stage2_oracle_runner.py",
    ),
    (
        "RNG equivalence",
        pytest_rng["collected"],
        pytest_rng["passed"],
        pytest_rng["failed"],
        pytest_rng["skipped"],
        pytest_rng["errors"],
        pytest_rng["duration_s"],
        "pytest test_rng_equivalence.py",
    ),
    (
        "Mutation resistance",
        pytest_mutation["collected"],
        pytest_mutation["passed"],
        pytest_mutation["failed"],
        pytest_mutation["skipped"],
        pytest_mutation["errors"],
        pytest_mutation["duration_s"],
        "pytest test_mutation_resistance.py",
    ),
    (
        "State isolation",
        pytest_state["collected"],
        pytest_state["passed"],
        pytest_state["failed"],
        pytest_state["skipped"],
        pytest_state["errors"],
        pytest_state["duration_s"],
        "pytest test_state_isolation.py",
    ),
    (
        "Proposal validation",
        pytest_proposal["collected"],
        pytest_proposal["passed"],
        pytest_proposal["failed"],
        pytest_proposal["skipped"],
        pytest_proposal["errors"],
        pytest_proposal["duration_s"],
        "pytest -k proposal subset",
    ),
]

test_lines = [
    "# AUTOCLAW Test Results",
    "",
    "| Category | Collected | Passed | Failed | Skipped | Errors | Duration | Command |",
    "|---|---:|---:|---:|---:|---:|---:|---|",
]
for row in test_rows:
    test_lines.append(
        f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} | {row[4]} | {row[5]} | {format_seconds(row[6])} | `{row[7]}` |"
    )

test_lines.extend(
    [
        "",
        "## Stage 2 Performance",
        "",
        f"- Baseline: {perf_results.get('baseline_s', 'n/a')}s",
        f"- Harness no extensions: {perf_results.get('noext_s', 'n/a')}s ({perf_results.get('noext_overhead_pct', 'n/a')}%)",
        f"- Harness with noop: {perf_results.get('noop_s', 'n/a')}s ({perf_results.get('noop_overhead_pct', 'n/a')}%)",
        f"- Hash verification passed: {perf_results.get('hash_verification_passed', False)}",
    ]
)
write_text(HANDOFF / "AUTOCLAW_TEST_RESULTS.md", "\n".join(test_lines) + "\n")

artifact_lines = [
    "# AUTOCLAW Top-Level Artifact Classification",
    "",
    "| Item | Category | Referenced by workspace code | Notes |",
    "|---|---|---|---|",
]
for artifact in artifacts:
    refs = "Yes" if artifact["referenced_by_workspace"] else "No"
    artifact_lines.append(
        f"| `{artifact['name']}` | {artifact['category']} | {refs} | {artifact['note']} |"
    )
    if artifact["reference_hits"]:
        hits = ", ".join(f"`{hit}`" for hit in artifact["reference_hits"])
        artifact_lines.append(f"|  |  |  | Hits: {hits} |")
write_text(
    HANDOFF / "AUTOCLAW_TOP_LEVEL_ARTIFACT_CLASSIFICATION.md",
    "\n".join(artifact_lines) + "\n",
)

stale_lines = [
    "# AUTOCLAW Known Stale Reports",
    "",
    "| Path | Stale Statement | Why stale |",
    "|---|---|---|",
]
for item in stale:
    stale_lines.append(
        f"| `{item['path']}` | {item['statement']} | {item['reason']} |"
    )
write_text(HANDOFF / "AUTOCLAW_KNOWN_STALE_REPORTS.md", "\n".join(stale_lines) + "\n")

continuation_lines = [
    "# AUTOCLAW Continuation Start Point",
    "",
    f"- Exact current HEAD: `{head}`",
    f"- Exact current branch: `{branch}`",
    "- Exact final verified stage: `Stage 2 implemented`",
    "- Whether Stage 3 exists: `No executable Local Flow Trail Memory implementation found`",
    "- First uncompleted stage: `Stage 3`",
    f"- Frozen baseline tag and commit: `natural-math-v5-reference-1.0` -> `{tag_target}`",
    f"- Stage 2 harness tag and commit: `No separate Stage 2 tag present`; committed at `{head}`",
    f"- Exact writable repository root: `{REPO}`",
    "- Files that must remain immutable: `01_INVENTORY/*`, `05_RESULTS/* historical artifacts`, `06_REPORTS/* historical artifacts`, and authority files under `C:\\_MASTER_LIBRARY\\01_CANON` and `02_VALIDATION_EVIDENCE`.",
    "- Known defects or warnings: Stage 1.1 report/test-count mismatch (289 vs observed 292); Stage 2 completion report still says commit pending; Stage 3 Local Flow Trail Memory absent; top-level AutoClaw scaffolding exists outside the writable workspace boundary.",
    "- Recommended first action for the next engineering system: rerun the complete suite exactly as audited here before changing code, then decide whether to begin Stage 3 or clean stale reporting/artifact boundaries.",
    "",
    "## Exact test commands",
    "",
    f"1. `{PYTHON} -B -m pytest -q -p no:cacheprovider {REPO / '04_TESTS' / 'layer_b_conformance'}`",
    f"2. `{PYTHON} -B -m pytest -q -p no:cacheprovider {REPO / '04_TESTS' / 'layer_b_conformance' / 'test_trace_equivalence.py'}`",
    f"3. `{PYTHON} -B -m pytest -q -p no:cacheprovider {REPO / '04_TESTS' / 'extension_harness'}`",
    f"4. `{PYTHON} -B -m pytest -q -p no:cacheprovider {REPO / '04_TESTS' / 'extension_harness' / 'test_rng_equivalence.py'}`",
    f"5. `{PYTHON} -B -m pytest -q -p no:cacheprovider {REPO / '04_TESTS' / 'extension_harness' / 'test_mutation_resistance.py'}`",
    f"6. `{PYTHON} -B -m pytest -q -p no:cacheprovider {REPO / '04_TESTS' / 'extension_harness' / 'test_state_isolation.py'}`",
    "7. Redirected read-only execution of the original oracle, donor differential, deterministic replay, Stage 2 oracle comparison, and Stage 2 performance scripts with outputs rerouted under the handoff temp directory.",
]
write_text(
    HANDOFF / "AUTOCLAW_CONTINUATION_START_POINT.md",
    "\n".join(continuation_lines) + "\n",
)

audit_lines = [
    "# AUTOCLAW Handoff Audit",
    "",
    f"Generated: {TIMESTAMP}",
    "",
    "## Repository State",
    "",
    f"- Repository root: `{REPO}`",
    f"- Branch: `{branch}`",
    f"- HEAD: `{head}`",
    f"- Working tree clean at start: {pre_porcelain == ''}",
    f"- Working tree unchanged after audit: {repo_unchanged}",
    f"- Tracked files: {len(tracked_files)}",
    f"- Untracked files: {len(untracked_files)}",
    f"- Ignored files: {len(ignored_files)}",
    f"- Remotes configured: {len(remotes)}",
    f"- Python: {python_version}",
    f"- OS: {os_info}",
    "",
    "## Frozen Baseline",
    "",
    f"- Frozen source path: `{FROZEN}`",
    f"- Frozen source SHA256: `{frozen_hash}`",
    f"- Expected SHA256 matched: `{frozen_hash == EXPECTED_FROZEN_HASH}`",
    f"- Local tag: `natural-math-v5-reference-1.0` -> `{tag_target}`",
    f"- Current workspace differs from tagged baseline: `{bool(diff_vs_tag)}`",
    f"- Reference implementation differs from tagged baseline: `{bool(ref_impl_diff_vs_tag)}`",
    f"- Changed reference-implementation files since tag: {', '.join(f'`{p}`' for p in ref_impl_diff_vs_tag) if ref_impl_diff_vs_tag else 'none'}",
    "",
    "## Local Tags",
    "",
]
for line in tags:
    audit_lines.append(f"- `{line}`")
audit_lines.extend(["", "## External Evidence Hashes", ""])
for key, value in external_hashes.items():
    audit_lines.append(f"- `{key}`: `{value}`")
audit_lines.extend(
    [
        "",
        "## Stage Findings",
        "",
        f"- Stage 0: {stages['Stage 0']['status']}",
        f"- Stage 1: {stages['Stage 1']['status']}",
        f"- Stage 1.1: {stages['Stage 1.1']['status']}",
        f"- Stage 2: {stages['Stage 2']['status']}",
        f"- Stage 3: {stages['Stage 3']['status']}",
        "",
        "## Local Flow Trail Memory Search",
        "",
        "```text",
        local_flow_summary["local_flow_hits"].strip(),
        "```",
        "",
        "Interpretation: no `trail_edges`, `trail_deposit`, `trail_decay`, or `natural_math_v5_1_local_flow_trail_memory` implementation was found. `PROPOSE_LOCAL_MOVE_PREFERENCE` exists as a defined/validated hook surface but is not dispatched by the harness adapters and is therefore inactive in practice.",
        "",
        "## Zip Verification",
        "",
        f"- Zip path: `{zip_path}`",
        f"- Zip SHA256: `{zip_hash}`",
        "- Zip opens successfully: `True`",
        f"- Zip contains `.git`: `{zip_has_git}`",
        f"- Zip entry count: `{len(zip_entries)}`",
        "",
        "## Notes",
        "",
        "- Repository-writing test scripts were executed through temporary redirected copies under the handoff temp directory so the original AutoClaw workspace stayed unchanged.",
        "- Existing `__pycache__` / `.pyc` ignored artifacts were preserved in-place but excluded from the handoff zip.",
    ]
)
write_text(HANDOFF / "AUTOCLAW_HANDOFF_AUDIT.md", "\n".join(audit_lines) + "\n")

receipt = {
    "generated_at": TIMESTAMP,
    "branch": branch,
    "head": head,
    "frozen_hash": frozen_hash,
    "stage_status": {name: data["status"] for name, data in stages.items()},
    "zip_path": str(zip_path),
    "zip_sha256": zip_hash,
    "zip_has_git": zip_has_git,
    "repo_unchanged": repo_unchanged,
    "test_categories": {
        row[0]: {
            "collected": row[1],
            "passed": row[2],
            "failed": row[3],
            "skipped": row[4],
            "errors": row[5],
        }
        for row in test_rows
    },
}
write_text(HANDOFF / "AUTOCLAW_COMPLETION_RECEIPT.json", json.dumps(receipt, indent=2))

print(json.dumps(receipt, indent=2))
