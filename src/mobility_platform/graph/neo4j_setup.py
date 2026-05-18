from __future__ import annotations

import argparse
import time
from pathlib import Path

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable

from mobility_platform.common.io import read_jsonl


def _connect_driver_with_retry(uri: str, user: str, password: str, *, timeout_s: float = 60.0):
    driver = GraphDatabase.driver(uri, auth=(user, password))
    deadline = time.time() + timeout_s
    last_err: Exception | None = None
    while time.time() < deadline:
        try:
            driver.verify_connectivity()
            return driver
        except ServiceUnavailable as e:
            last_err = e
            time.sleep(1.0)
    driver.close()
    raise SystemExit(f"Neo4j not ready at {uri} after {timeout_s:.0f}s: {last_err}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uri", type=str, required=True)
    p.add_argument("--user", type=str, required=True)
    p.add_argument("--password", type=str, required=True)
    p.add_argument("--data", type=str, required=True)
    args = p.parse_args()

    data_dir = Path(args.data)
    users = list(read_jsonl(data_dir / "users.jsonl"))
    stations = list(read_jsonl(data_dir / "stations.jsonl"))
    trips = list(read_jsonl(data_dir / "trips.jsonl"))

    driver = _connect_driver_with_retry(args.uri, args.user, args.password)
    with driver.session() as session:
        # reset
        session.run("MATCH (n) DETACH DELETE n")
        # constraints
        session.run("CREATE CONSTRAINT user_id IF NOT EXISTS FOR (u:USER) REQUIRE u.user_id IS UNIQUE")
        session.run("CREATE CONSTRAINT station_id IF NOT EXISTS FOR (s:STATION) REQUIRE s.station_id IS UNIQUE")
        session.run("CREATE CONSTRAINT trip_id IF NOT EXISTS FOR (t:TRIP) REQUIRE t.trip_id IS UNIQUE")

        session.run(
            """
            UNWIND $rows AS r
            MERGE (u:USER {user_id: r.user_id})
            SET u.name = r.name, u.surname = r.surname, u.birthdate = r.birthdate, u.country = r.country
            """,
            rows=users,
        )
        session.run(
            """
            UNWIND $rows AS r
            MERGE (s:STATION {station_id: r.station_id})
            SET s.name = r.name, s.city = r.city, s.capacity = r.capacity
            """,
            rows=stations,
        )
        session.run(
            """
            UNWIND $rows AS r
            MERGE (t:TRIP {trip_id: r.trip_id})
            SET t.start_time = r.start_time, t.end_time = r.end_time, t.cost = r.cost
            WITH t, r
            MATCH (u:USER {user_id: r.user_id})
            MATCH (ss:STATION {station_id: r.start_station_id})
            MATCH (es:STATION {station_id: r.end_station_id})
            MERGE (u)-[:PERFORMED]->(t)
            MERGE (t)-[:STARTS_AT]->(ss)
            MERGE (t)-[:ENDS_AT]->(es)
            """,
            rows=trips,
        )

    driver.close()
    print(f"Loaded Neo4j: users={len(users)} stations={len(stations)} trips={len(trips)}")


if __name__ == "__main__":
    main()

