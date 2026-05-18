from __future__ import annotations

import argparse
from pathlib import Path

from pymongo import MongoClient

from mobility_platform.common.io import read_jsonl


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uri", type=str, required=True)
    p.add_argument("--db", type=str, required=True)
    p.add_argument("--data", type=str, required=True)
    args = p.parse_args()

    data_dir = Path(args.data)

    client = MongoClient(args.uri)
    db = client[args.db]

    trips_col = db["trips"]
    trips_col.drop()

    docs = list(read_jsonl(data_dir / "trip_docs.jsonl"))
    if docs:
        trips_col.insert_many(docs, ordered=False)

    trips_col.create_index("user.user_id")
    trips_col.create_index("start_station.station_id")
    trips_col.create_index("end_station.station_id")
    trips_col.create_index("events.type")

    print(f"Loaded MongoDB db={args.db} collection=trips docs={len(docs)}")


if __name__ == "__main__":
    main()

