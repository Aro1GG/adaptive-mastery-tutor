#!/usr/bin/env python3
"""
tutor.py — Adaptive Tutor data management CLI.

Manages student progress files and knowledge point queries.
All data stored as JSON in ./students/ relative to this script.
Knowledge points defined in knowledge-points.yaml (in skill directory or cwd).
"""

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
STUDENTS_DIR = SCRIPT_DIR / "students"


def get_student_path(name: str) -> Path:
    """Get the JSON file path for a student."""
    safe = name.strip().replace(" ", "_").lower()
    return STUDENTS_DIR / f"{safe}.json"


def load_student(name: str) -> dict:
    """Load a student's progress file. Returns empty template if not found."""
    path = get_student_path(name)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "name": name,
        "current_topic": "",
        "knowledge_points": {}
    }


def save_student(name: str, data: dict):
    """Save a student's progress file."""
    STUDENTS_DIR.mkdir(parents=True, exist_ok=True)
    path = get_student_path(name)
    data["name"] = name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_knowledge_points() -> dict:
    """Load knowledge-points.yaml from cwd or skill directory."""
    import yaml
    candidates = [
        Path.cwd() / "knowledge-points.yaml",
        SCRIPT_DIR / "knowledge-points.yaml",
    ]
    for p in candidates:
        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
    print("Error: knowledge-points.yaml not found in cwd or skill directory", file=sys.stderr)
    sys.exit(1)


def cmd_student_list():
    """List all students."""
    STUDENTS_DIR.mkdir(parents=True, exist_ok=True)
    students = sorted(STUDENTS_DIR.glob("*.json"))
    if not students:
        print("No students found.")
        return
    for s in students:
        data = json.loads(s.read_text(encoding="utf-8"))
        kps = data.get("knowledge_points", {})
        mastered = sum(1 for v in kps.values() if v.get("status") == "mastered")
        total = len(kps)
        print(f"  {data['name']}  [{mastered}/{total} mastered]  topic: {data.get('current_topic', '-')}")


def cmd_student_show(args):
    """Show a student's full progress."""
    data = load_student(args.name)
    print(json.dumps(data, ensure_ascii=False, indent=2))


def cmd_student_create(args):
    """Create a new student."""
    path = get_student_path(args.name)
    if path.exists():
        print(f"Student '{args.name}' already exists.")
        sys.exit(1)
    data = {
        "name": args.name,
        "current_topic": "",
        "knowledge_points": {}
    }
    save_student(args.name, data)
    print(f"Created student: {args.name}")


def cmd_student_delete(args):
    """Delete a student."""
    path = get_student_path(args.name)
    if not path.exists():
        print(f"Student '{args.name}' not found.")
        sys.exit(1)
    path.unlink()
    print(f"Deleted student: {args.name}")


def cmd_knowledge_list():
    """List all knowledge points with dependency info."""
    kp_data = load_knowledge_points()
    kps = kp_data.get("knowledge_points", [])
    print(f"Topic: {kp_data.get('topic', '(unnamed)')}")
    print(f"Total knowledge points: {len(kps)}\n")
    for kp in kps:
        prereqs = ", ".join(kp.get("prerequisites", [])) or "none"
        level = kp.get("bloom_level", "remember")
        print(f"  [{level}] {kp['id']}: {kp['name']}")
        print(f"        prerequisites: {prereqs}")


def cmd_knowledge_next(args):
    """Show the next knowledge point(s) a student should work on."""
    data = load_student(args.name)
    kp_data = load_knowledge_points()
    kps = kp_data.get("knowledge_points", [])
    progress = data.get("knowledge_points", {})

    mastered = {
        kp_id for kp_id, v in progress.items()
        if v.get("status") == "mastered"
    }

    results = []
    for kp in kps:
        kp_id = kp["id"]
        status = progress.get(kp_id, {}).get("status", "not_started")
        if status == "mastered":
            continue
        prereqs = set(kp.get("prerequisites", []))
        blocked = prereqs - mastered
        results.append({
            "id": kp_id,
            "name": kp["name"],
            "level": kp.get("bloom_level", "remember"),
            "status": status,
            "blocked": bool(blocked),
            "blocked_by": list(blocked),
            "weak_areas": progress.get(kp_id, {}).get("weak_areas", []),
        })

    if not results:
        print(f"All knowledge points mastered! 🎉")
        return

    def sort_key(r):
        priority = 0 if r["status"] == "in_progress" else 1 if not r["blocked"] else 2
        return (priority, r["id"])

    results.sort(key=sort_key)

    print(f"Next for {args.name}:\n")
    for r in results:
        icon = "🔴" if r["blocked"] else "🟡" if r["status"] == "in_progress" else "⚪"
        weak = f"  weak: {', '.join(r['weak_areas'])}" if r["weak_areas"] else ""
        blocked = f"  blocked by: {', '.join(r['blocked_by'])}" if r["blocked"] else ""
        print(f"  {icon} [{r['level']}] {r['id']}: {r['name']}  ({r['status']})")
        if weak:
            print(weak)
        if blocked:
            print(blocked)


def cmd_knowledge_unlocked(args):
    """Show knowledge points a student can access (prerequisites met)."""
    data = load_student(args.name)
    kp_data = load_knowledge_points()
    kps = kp_data.get("knowledge_points", [])
    progress = data.get("knowledge_points", {})

    mastered = {
        kp_id for kp_id, v in progress.items()
        if v.get("status") == "mastered"
    }

    for kp in kps:
        kp_id = kp["id"]
        status = progress.get(kp_id, {}).get("status", "not_started")
        if status == "mastered":
            continue
        prereqs = set(kp.get("prerequisites", []))
        if prereqs <= mastered:
            print(f"  [{kp.get('bloom_level', 'remember')}] {kp_id}: {kp['name']}")


def cmd_student_update(args):
    """Update a knowledge point's status for a student."""
    data = load_student(args.name)
    kp_data = load_knowledge_points()
    kps = {kp["id"]: kp for kp in kp_data.get("knowledge_points", [])}

    if args.kp_id not in kps:
        print(f"Knowledge point '{args.kp_id}' not found.")
        sys.exit(1)

    progress = data.setdefault("knowledge_points", {})
    entry = progress.setdefault(args.kp_id, {
        "status": "not_started",
        "attempts": 0,
        "quiz_history": []
    })

    if args.status:
        valid = {"not_started", "in_progress", "mastered"}
        if args.status not in valid:
            print(f"Invalid status. Use one of: {', '.join(valid)}")
            sys.exit(1)
        entry["status"] = args.status

    if args.increment_attempt:
        entry["attempts"] = entry.get("attempts", 0) + 1

    if args.weak_areas:
        entry["weak_areas"] = [w.strip() for w in args.weak_areas.split(",")]

    if args.passed is not None:
        import datetime
        quiz_record = {
            "date": datetime.date.today().isoformat(),
            "level": args.level or "unknown",
            "passed": args.passed,
            "score": args.score or "-",
            "notes": args.notes or ""
        }
        entry.setdefault("quiz_history", []).append(quiz_record)

    save_student(args.name, data)
    print(f"Updated {args.name}/{args.kp_id}: status={entry['status']}, attempts={entry.get('attempts', 0)}")


def cmd_stats(args):
    """Generate a mastery report for a student."""
    data = load_student(args.name)
    kp_data = load_knowledge_points()
    kps = kp_data.get("knowledge_points", [])
    progress = data.get("knowledge_points", {})

    total = len(kps)
    if total == 0:
        print("No knowledge points defined.")
        return

    mastered = sum(1 for kp in kps if progress.get(kp["id"], {}).get("status") == "mastered")
    in_progress = sum(1 for kp in kps if progress.get(kp["id"], {}).get("status") == "in_progress")
    not_started = total - mastered - in_progress

    print(f"\n{'='*50}")
    print(f"  Student: {args.name}")
    print(f"  Topic: {kp_data.get('topic', '-')}")
    print(f"{'='*50}")
    print(f"  Mastered:    {mastered}/{total}  ({mastered*100//total if total else 0}%)")
    print(f"  In Progress: {in_progress}/{total}")
    print(f"  Not Started: {not_started}/{total}")
    print(f"{'='*50}")

    levels = {"remember": "L1-识记", "understand": "L2-理解", "apply": "L3-应用"}
    print(f"\n  By Cognitive Level:")
    for key, label in levels.items():
        level_kps = [kp for kp in kps if kp.get("bloom_level") == key]
        level_mastered = sum(1 for kp in level_kps if progress.get(kp["id"], {}).get("status") == "mastered")
        if level_kps:
            bar = "█" * (level_mastered * 20 // len(level_kps))
            print(f"  {label}: {bar} {level_mastered}/{len(level_kps)}")

    weak = [(kp_id, v.get("weak_areas", [])) for kp_id, v in progress.items() if v.get("weak_areas")]
    if weak:
        print(f"\n  ⚠ Weak Areas:")
        for kp_id, areas in weak:
            kp_name = next((kp["name"] for kp in kps if kp["id"] == kp_id), kp_id)
            print(f"    {kp_name}: {', '.join(areas)}")

    print(f"{'='*50}\n")


def cmd_stats_all():
    """Show overview for all students."""
    STUDENTS_DIR.mkdir(parents=True, exist_ok=True)
    students = sorted(STUDENTS_DIR.glob("*.json"))
    if not students:
        print("No students found.")
        return

    kp_data = load_knowledge_points()
    total_kps = len(kp_data.get("knowledge_points", []))

    print(f"\n{'='*60}")
    print(f"  Class Overview  |  Topic: {kp_data.get('topic', '-')}  |  {len(students)} students")
    print(f"{'='*60}")
    for s in students:
        data = json.loads(s.read_text(encoding="utf-8"))
        progress = data.get("knowledge_points", {})
        mastered = sum(1 for v in progress.values() if v.get("status") == "mastered")
        in_prog = sum(1 for v in progress.values() if v.get("status") == "in_progress")
        pct = mastered * 100 // total_kps if total_kps else 0
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"  {data['name']:20s} {bar} {pct}%  ({mastered}/{total_kps})  [{in_prog} in progress]")
    print(f"{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Adaptive Tutor — student progress manager")
    sub = parser.add_subparsers(dest="command", help="Subcommand")

    p_student = sub.add_parser("student", help="Student operations")
    p_student_sub = p_student.add_subparsers(dest="action")

    p_list = p_student_sub.add_parser("list", help="List all students")
    p_list.set_defaults(func=lambda a: cmd_student_list())

    p_show = p_student_sub.add_parser("show", help="Show student progress")
    p_show.add_argument("name", help="Student name")
    p_show.set_defaults(func=cmd_student_show)

    p_create = p_student_sub.add_parser("create", help="Create a new student")
    p_create.add_argument("name", help="Student name")
    p_create.set_defaults(func=cmd_student_create)

    p_del = p_student_sub.add_parser("delete", help="Delete a student")
    p_del.add_argument("name", help="Student name")
    p_del.set_defaults(func=cmd_student_delete)

    p_upd = p_student_sub.add_parser("update", help="Update a knowledge point status")
    p_upd.add_argument("name", help="Student name")
    p_upd.add_argument("kp_id", help="Knowledge point ID")
    p_upd.add_argument("--status", help="New status (not_started|in_progress|mastered)")
    p_upd.add_argument("--increment-attempt", action="store_true", help="Increment attempt counter")
    p_upd.add_argument("--weak-areas", help="Comma-separated weak areas")
    p_upd.add_argument("--passed", type=lambda x: x.lower() == "true", help="Quiz passed? true/false")
    p_upd.add_argument("--level", help="Bloom level of this quiz")
    p_upd.add_argument("--score", help="Score string e.g. 3/4")
    p_upd.add_argument("--notes", help="Quiz notes")
    p_upd.set_defaults(func=cmd_student_update)

    p_know = sub.add_parser("knowledge", help="Knowledge point operations")
    p_know_sub = p_know.add_subparsers(dest="action")

    p_kl = p_know_sub.add_parser("list", help="List all knowledge points")
    p_kl.set_defaults(func=lambda a: cmd_knowledge_list())

    p_kn = p_know_sub.add_parser("next", help="Show next knowledge points for student")
    p_kn.add_argument("name", help="Student name")
    p_kn.set_defaults(func=cmd_knowledge_next)

    p_ku = p_know_sub.add_parser("unlocked", help="Show unlocked knowledge points for student")
    p_ku.add_argument("name", help="Student name")
    p_ku.set_defaults(func=cmd_knowledge_unlocked)

    p_stats = sub.add_parser("stats", help="Statistics and reports")
    p_stats_sub = p_stats.add_subparsers(dest="action")

    p_ss = p_stats_sub.add_parser("show", help="Show student stats")
    p_ss.add_argument("name", help="Student name")
    p_ss.set_defaults(func=cmd_stats)

    p_sa = p_stats_sub.add_parser("all", help="Class overview")
    p_sa.set_defaults(func=lambda a: cmd_stats_all())

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
