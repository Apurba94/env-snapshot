"""Command-line interface for env-snapshot."""
import argparse
import json
import sys

from .core import diff_snapshots, save, snapshot, to_markdown


def main(argv=None):
    ap = argparse.ArgumentParser(prog="env-snapshot", description="Record or compare computational environments.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture", help="record the current environment")
    c.add_argument("-o", "--output", default="environment.json")
    c.add_argument("--markdown", help="also write a Markdown summary (e.g. for a methods appendix)")
    c.add_argument("--project", default=".", help="project directory for git information")
    c.add_argument("--hash", nargs="*", default=[], help="input files to fingerprint")
    c.add_argument("--no-packages", action="store_true")
    d = sub.add_parser("diff", help="compare two snapshots")
    d.add_argument("old")
    d.add_argument("new")
    args = ap.parse_args(argv)
    if args.cmd == "capture":
        s = snapshot(args.project, args.hash, not args.no_packages)
        save(s, args.output)
        if args.markdown:
            with open(args.markdown, "w", encoding="utf-8") as fh:
                fh.write(to_markdown(s))
        print("environment saved to %s (%d packages)" % (args.output, len(s.get("packages", {}))))
        return 0
    with open(args.old, encoding="utf-8") as fh:
        a = json.load(fh)
    with open(args.new, encoding="utf-8") as fh:
        b = json.load(fh)
    diffs = diff_snapshots(a, b)
    for line in diffs:
        print(line)
    print("%d difference(s)" % len(diffs), file=sys.stderr)
    return 1 if diffs else 0
