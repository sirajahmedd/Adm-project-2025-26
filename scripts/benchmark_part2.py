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
    p.add_argument("--data-dir", type=str, default="data_bench_graph")
    p.add_argument("--neo4j-uri", type=str, default="bolt://localhost:7687")
    p.add_argument("--neo4j-user", type=str, default="neo4j")
    p.add_argument("--neo4j-password", type=str, default="neo4j_password")
    args = p.parse_args()

    out_path = Path(args.out)
    data_root = Path(args.data_dir)
    data_root.mkdir(parents=True, exist_ok=True)

    users_sizes = [1000, 10000]
    trips_sizes = [10000, 50000]
    events_per_trip = [0, 2]

    results: list[dict] = []
    for u in users_sizes:
        for t in trips_sizes:
            for ept in events_per_trip:
                tag = f"u{u}_t{t}_e{ept}"
                data_dir = data_root / tag
                data_dir.mkdir(parents=True, exist_ok=True)

                t0 = time.perf_counter()
                _cmd(
                    [
                        "python",
                        "-m",
                        "mobility_platform.data_gen.generate",
                        "--out",
                        str(data_dir),
                        "--users",
                        str(u),
                        "--stations",
                        "200",
                        "--trips",
                        str(t),
                        "--events-per-trip",
                        str(ept),
                    ]
                )
                gen_s = time.perf_counter() - t0

                t1 = time.perf_counter()
                _cmd(
                    [
                        "python",
                        "-m",
                        "mobility_platform.graph.neo4j_setup",
                        "--uri",
                        args.neo4j_uri,
                        "--user",
                        args.neo4j_user,
                        "--password",
                        args.neo4j_password,
                        "--data",
                        str(data_dir),
                    ]
                )
                load_s = time.perf_counter() - t1

                # pick a deterministic user id (exists when u >= 1)
                sample_user = "u_000001"
                t2 = time.perf_counter()
                _cmd(
                    [
                        "python",
                        "-m",
                        "mobility_platform.graph.queries",
                        "--uri",
                        args.neo4j_uri,
                        "--user",
                        args.neo4j_user,
                        "--password",
                        args.neo4j_password,
                        "--query",
                        "1",
                        "--user-id",
                        sample_user,
                        "--limit",
                        "1",
                    ]
                )
                q1_s = time.perf_counter() - t2

                t3 = time.perf_counter()
                _cmd(
                    [
                        "python",
                        "-m",
                        "mobility_platform.graph.queries",
                        "--uri",
                        args.neo4j_uri,
                        "--user",
                        args.neo4j_user,
                        "--password",
                        args.neo4j_password,
                        "--query",
                        "2",
                        "--limit",
                        "3",
                    ]
                )
                q2_s = time.perf_counter() - t3

                results.append(
                    {
                        "tag": tag,
                        "users": u,
                        "trips": t,
                        "events_per_trip": ept,
                        "gen_s": gen_s,
                        "neo4j_load_s": load_s,
                        "q1_reachable_stations_s": q1_s,
                        "q2_top3_stations_s": q2_s,
                    }
                )

                out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
                print(f"Wrote partial results -> {out_path}")

    print(f"Done -> {out_path}")


if __name__ == "__main__":
    main()

