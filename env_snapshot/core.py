"""Collect OS, hardware, Python, package and git information; compare two snapshots."""
import datetime
import hashlib
import json
import os
import platform
import subprocess
import sys

try:
    from importlib import metadata
except ImportError:  # pragma: no cover
    metadata = None

# Only these environment variables are recorded; never record secrets.
SAFE_ENV = ("CONDA_DEFAULT_ENV", "VIRTUAL_ENV", "PYTHONHASHSEED", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
            "OPENBLAS_NUM_THREADS", "CUDA_VISIBLE_DEVICES", "LANG", "LC_ALL", "TZ", "SLURM_JOB_ID", "PBS_JOBID")


def _run(cmd, cwd=None):
    try:
        r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def git_info(path="."):
    commit = _run(["git", "rev-parse", "HEAD"], path)
    if not commit:
        return None
    status = _run(["git", "status", "--porcelain"], path) or ""
    return {"commit": commit, "branch": _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], path),
            "dirty": bool(status), "changed_files": len(status.splitlines()),
            "remote": _run(["git", "config", "--get", "remote.origin.url"], path)}


def packages():
    if metadata is None:
        return {}
    out = {}
    for d in metadata.distributions():
        name = d.metadata.get("Name")
        if name:
            out[name.lower()] = d.version
    return dict(sorted(out.items()))


def snapshot(project_dir=".", extra_files=(), include_packages=True):
    snap = {
        "created": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "os": {"system": platform.system(), "release": platform.release(), "version": platform.version(),
               "machine": platform.machine()},
        "hardware": {"cpu_count": os.cpu_count(), "processor": platform.processor()},
        "python": {"version": platform.python_version(), "implementation": platform.python_implementation(),
                   "executable": sys.executable, "prefix": sys.prefix},
        "env": {k: os.environ[k] for k in SAFE_ENV if k in os.environ},
        "git": git_info(project_dir),
        "files": {},
    }
    if include_packages:
        snap["packages"] = packages()
    for f in extra_files:
        if os.path.isfile(f):
            h = hashlib.sha256()
            with open(f, "rb") as fh:
                for chunk in iter(lambda: fh.read(1 << 20), b""):
                    h.update(chunk)
            snap["files"][f] = h.hexdigest()
    return snap


def diff_snapshots(a, b):
    """Return a list of human-readable differences between two snapshots."""
    out = []
    for section in ("os", "python", "hardware", "env"):
        for k in sorted(set(a.get(section, {})) | set(b.get(section, {}))):
            va, vb = a.get(section, {}).get(k), b.get(section, {}).get(k)
            if va != vb and k not in ("executable", "prefix", "version" if section == "os" else ""):
                out.append("%s.%s: %s -> %s" % (section, k, va, vb))
    pa, pb = a.get("packages", {}), b.get("packages", {})
    for p in sorted(set(pa) | set(pb)):
        if p not in pb:
            out.append("package removed: %s %s" % (p, pa[p]))
        elif p not in pa:
            out.append("package added: %s %s" % (p, pb[p]))
        elif pa[p] != pb[p]:
            out.append("package changed: %s %s -> %s" % (p, pa[p], pb[p]))
    ga, gb = a.get("git") or {}, b.get("git") or {}
    if ga.get("commit") != gb.get("commit"):
        out.append("git commit: %s -> %s" % ((ga.get("commit") or "-")[:10], (gb.get("commit") or "-")[:10]))
    for f in sorted(set(a.get("files", {})) | set(b.get("files", {}))):
        if a.get("files", {}).get(f) != b.get("files", {}).get(f):
            out.append("file changed: %s" % f)
    return out


def to_markdown(s):
    lines = ["# Computational environment", "", "Recorded %s" % s["created"], "",
             "- **OS:** %s %s (%s)" % (s["os"]["system"], s["os"]["release"], s["os"]["machine"]),
             "- **CPU cores:** %s" % s["hardware"]["cpu_count"],
             "- **Python:** %s %s" % (s["python"]["implementation"], s["python"]["version"])]
    g = s.get("git")
    if g:
        lines.append("- **Code version:** git %s on %s%s" % (g["commit"][:10], g["branch"],
                                                            " (uncommitted changes: %d files)" % g["changed_files"] if g["dirty"] else ""))
    for k, v in s.get("env", {}).items():
        lines.append("- `%s` = `%s`" % (k, v))
    if s.get("packages"):
        lines += ["", "## Packages (%d)" % len(s["packages"]), "", "```"]
        lines += ["%s==%s" % kv for kv in s["packages"].items()]
        lines.append("```")
    if s.get("files"):
        lines += ["", "## Input files (SHA-256)", ""] + ["- `%s` %s" % (f, h[:16]) for f, h in s["files"].items()]
    return "\n".join(lines) + "\n"


def save(s, path):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(s, fh, indent=2)
