from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from faker import Faker

from mobility_platform.common.constants import EVENT_TYPES
from mobility_platform.common.io import write_jsonl


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _make_id(prefix: str, i: int, width: int = 6) -> str:
    return f"{prefix}_{i:0{width}d}"


def gen_users(fake: Faker, n_users: int) -> List[Dict[str, Any]]:
    users: List[Dict[str, Any]] = []
    for i in range(1, n_users + 1):
        users.append(
            {
                "user_id": _make_id("u", i),
                "name": fake.first_name(),
                "surname": fake.last_name(),
                "birthdate": fake.date_of_birth(minimum_age=18, maximum_age=80).isoformat(),
                "country": fake.country(),
            }
        )
    return users


def gen_stations(fake: Faker, n_stations: int) -> List[Dict[str, Any]]:
    italian_cities = [
        "Rome",
        "Milan",
        "Naples",
        "Turin",
        "Palermo",
        "Genoa",
        "Bologna",
        "Florence",
        "Bari",
        "Catania",
    ]
    stations: List[Dict[str, Any]] = []
    for i in range(1, n_stations + 1):
        stations.append(
            {
                "station_id": _make_id("s", i),
                "name": f"Station {i}",
                "city": random.choice(italian_cities),
                "capacity": random.randint(5, 60),
            }
        )
    return stations


def _sample_event(ts: datetime) -> Dict[str, Any]:
    et = random.choice(EVENT_TYPES)
    if et == "GPS":
        value: Any = {
            "lat": round(random.uniform(35.0, 47.0), 6),
            "lon": round(random.uniform(6.0, 19.0), 6),
        }
    elif et == "BATTERY":
        value = {"pct": random.randint(0, 100)}
    elif et == "DELAY":
        value = {"seconds": random.randint(1, 900)}
    else:  # ERROR
        value = random.choice(
            [
                "E_MOTOR",
                "E_LOCK",
                "E_GPS",
                "E_BRAKE",
                "E_UNKNOWN",
            ]
        )
    return {
        "timestamp": ts.isoformat(),
        "type": et,
        "value": value,
    }


def gen_trips_and_events(
    n_trips: int,
    users: List[Dict[str, Any]],
    stations: List[Dict[str, Any]],
    events_per_trip: int,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    trips: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []

    now = _utc_now()
    for i in range(1, n_trips + 1):
        trip_id = _make_id("t", i)
        user = random.choice(users)
        start_station = random.choice(stations)
        end_station = random.choice(stations)

        start_time = now - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23), minutes=random.randint(0, 59))
        duration_min = random.randint(3, 120)
        end_time = start_time + timedelta(minutes=duration_min)
        cost = round(1.0 + 0.2 * duration_min + random.uniform(-0.5, 1.5), 2)

        trips.append(
            {
                "trip_id": trip_id,
                "user_id": user["user_id"],
                "start_station_id": start_station["station_id"],
                "end_station_id": end_station["station_id"],
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "cost": cost,
            }
        )

        n_events = events_per_trip if events_per_trip >= 0 else random.choice([0, 2, 5, 10])
        if n_events == 0:
            continue
        for j in range(n_events):
            ts = start_time + timedelta(seconds=int((j + 1) * (duration_min * 60 / (n_events + 1))))
            events.append(
                {
                    "event_id": _make_id("e", i * 1000 + j, width=9),
                    "trip_id": trip_id,
                    **_sample_event(ts),
                }
            )

    return trips, events


def gen_documents(
    users: List[Dict[str, Any]],
    stations: List[Dict[str, Any]],
    trips: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    # Document model: one document per trip embedding user/stations + events
    users_by_id = {u["user_id"]: u for u in users}
    stations_by_id = {s["station_id"]: s for s in stations}
    events_by_trip: Dict[str, List[Dict[str, Any]]] = {}
    for e in events:
        events_by_trip.setdefault(e["trip_id"], []).append(
            {
                "timestamp": e["timestamp"],
                "type": e["type"],
                "value": e["value"],
            }
        )

    docs: List[Dict[str, Any]] = []
    for t in trips:
        docs.append(
            {
                "_id": t["trip_id"],
                "trip_id": t["trip_id"],
                "user": users_by_id[t["user_id"]],
                "start_station": stations_by_id[t["start_station_id"]],
                "end_station": stations_by_id[t["end_station_id"]],
                "start_time": t["start_time"],
                "end_time": t["end_time"],
                "cost": t["cost"],
                "events": events_by_trip.get(t["trip_id"], []),
            }
        )
    return docs


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=str, required=True, help="Output folder (e.g. data)")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--users", type=int, required=True)
    p.add_argument("--stations", type=int, default=200)
    p.add_argument("--trips", type=int, required=True)
    p.add_argument("--events-per-trip", type=int, default=2, help="0,2,5,10 (or -1 to randomize)")
    args = p.parse_args()

    random.seed(args.seed)
    fake = Faker()
    Faker.seed(args.seed)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    users = gen_users(fake, args.users)
    stations = gen_stations(fake, args.stations)
    trips, events = gen_trips_and_events(args.trips, users, stations, args.events_per_trip)
    trip_docs = gen_documents(users, stations, trips, events)

    write_jsonl(out / "users.jsonl", users)
    write_jsonl(out / "stations.jsonl", stations)
    write_jsonl(out / "trips.jsonl", trips)
    write_jsonl(out / "events.jsonl", events)
    write_jsonl(out / "trip_docs.jsonl", trip_docs)

    print(
        f"Wrote: users={len(users)}, stations={len(stations)}, trips={len(trips)}, events={len(events)}, trip_docs={len(trip_docs)} -> {out}"
    )


if __name__ == "__main__":
    main()

