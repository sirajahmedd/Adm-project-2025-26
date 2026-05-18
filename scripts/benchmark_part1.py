from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from subprocess import run


def _cmd(args: list[str]) -> None:
    r = run(args, check=True)
    if r.returncode != 0:
        raise SystemExit(r.returncode)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=str, required=True)
    p.add_argument("--data-dir", type=str, default="data_bench")
    args = p.parse_args()

    out_path = Path(args.out)
    data_root = Path(args.data_dir)
    data_root.mkdir(parents=True, exist_ok=True)

    users_sizes = [1000, 10000]
    trips_sizes = [10000, 50000]
    events_per_trip = [0, 2, 5]

    results: list[dict] = []
    for u in users_sizes:
        for t in trips_sizes:
            for ept in events_per_trip:
                tag = f"u{u}_t{t}_e{ept}"
                data_dir = data_root / tag
                db_path = data_dir / "mobility.sqlite"
                data_dir.mkdir(parents=True, exist_ok=True)

                t0 = time.perf_counter()
                _cmd(["python", "-m", "mobility_platform.data_gen.generate", "--out", str(data_dir), "--users", str(u), "--stations", "200", "--trips", str(t), "--events-per-trip", str(ept)])
                gen_s = time.perf_counter() - t0

                t1 = time.perf_counter()
                _cmd(["python", "-m", "mobility_platform.relational.sqlite_setup", "--db", str(db_path), "--data", str(data_dir)])
                load_s = time.perf_counter() - t1

                q_times = {}
                for q in [1, 2, 3, 4]:
                    t2 = time.perf_counter()
                    _cmd(["python", "-m", "mobility_platform.relational.queries", "--db", str(db_path), "--query", str(q), "--limit", "1"])
                    q_times[f"q{q}_sqlite_s"] = time.perf_counter() - t2

                results.append(
                    {
                        "tag": tag,
                        "users": u,
                        "trips": t,
                        "events_per_trip": ept,
                        "gen_s": gen_s,
                        "sqlite_load_s": load_s,
                        **q_times,
                    }
                )

                out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
                print(f"Wrote partial results -> {out_path}")

    print(f"Done -> {out_path}")


if __name__ == "__main__":
    main()

