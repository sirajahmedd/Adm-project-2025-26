from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from mobility_platform.common.io import read_jsonl


def load_schema(conn: sqlite3.Connection, schema_path: Path) -> None:
    conn.executescript(schema_path.read_text(encoding="utf-8"))
    conn.commit()


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=str, required=True, help="SQLite db path (e.g. data/mobility.sqlite)")
    p.add_argument("--data", type=str, required=True, help="Folder containing *.jsonl generated data")
    p.add_argument("--schema", type=str, default=str(Path("sql") / "schema.sql"))
    args = p.parse_args()

    db_path = Path(args.db)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    data_dir = Path(args.data)
    schema_path = Path(args.schema)

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    load_schema(conn, schema_path)

    users = list(read_jsonl(data_dir / "users.jsonl"))
    stations = list(read_jsonl(data_dir / "stations.jsonl"))
    trips = list(read_jsonl(data_dir / "trips.jsonl"))
    events = list(read_jsonl(data_dir / "events.jsonl"))

    conn.executemany(
        "INSERT OR REPLACE INTO users(user_id,name,surname,birthdate,country) VALUES (?,?,?,?,?)",
        [(u["user_id"], u["name"], u["surname"], u["birthdate"], u["country"]) for u in users],
    )
    conn.executemany(
        "INSERT OR REPLACE INTO stations(station_id,name,city,capacity) VALUES (?,?,?,?)",
        [(s["station_id"], s["name"], s["city"], int(s["capacity"])) for s in stations],
    )
    conn.executemany(
        "INSERT OR REPLACE INTO trips(trip_id,user_id,start_station_id,end_station_id,start_time,end_time,cost) VALUES (?,?,?,?,?,?,?)",
        [
            (
                t["trip_id"],
                t["user_id"],
                t["start_station_id"],
                t["end_station_id"],
                t["start_time"],
                t["end_time"],
                float(t["cost"]),
            )
            for t in trips
        ],
    )
    conn.executemany(
        "INSERT OR REPLACE INTO events(event_id,trip_id,timestamp,type,value_json) VALUES (?,?,?,?,?)",
        [
            (e["event_id"], e["trip_id"], e["timestamp"], e["type"], json.dumps(e["value"], ensure_ascii=False))
            for e in events
        ],
    )
    conn.commit()

    print(f"Loaded into SQLite: {db_path} (users={len(users)}, stations={len(stations)}, trips={len(trips)}, events={len(events)})")


if __name__ == "__main__":
    main()

