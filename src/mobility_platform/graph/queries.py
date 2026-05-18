from __future__ import annotations

import argparse
import time
from typing import Any, Dict, List, Tuple

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable


def _connect_driver_with_retry(uri: str, user: str, password: str, *, timeout_s: float = 30.0):
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


def q1_reachable_stations(driver, user_id: str) -> List[Dict[str, Any]]:
    # Through trips: USER -> TRIP -> STARTS_AT/ENDS_AT -> STATION
    query = """
    MATCH (u:USER {user_id: $user_id})-[:PERFORMED]->(t:TRIP)
    MATCH (t)-[:STARTS_AT|ENDS_AT]->(s:STATION)
    RETURN DISTINCT s.station_id AS station_id, s.name AS name, s.city AS city
    ORDER BY station_id
    """
    with driver.session() as session:
        res = session.run(query, user_id=user_id)
        return [r.data() for r in res]


def q2_top3_important_stations(driver) -> List[Dict[str, Any]]:
    # Importance = incoming + outgoing based on trips (start/end)
    query = """
    MATCH (s:STATION)
    OPTIONAL MATCH (:TRIP)-[:STARTS_AT]->(s)
    WITH s, COUNT(*) AS incoming
    OPTIONAL MATCH (:TRIP)-[:ENDS_AT]->(s)
    WITH s, incoming, COUNT(*) AS outgoing
    RETURN s.station_id AS station_id, s.name AS name, s.city AS city,
           incoming, outgoing, (incoming + outgoing) AS total
    ORDER BY total DESC
    LIMIT 3
    """
    with driver.session() as session:
        res = session.run(query)
        return [r.data() for r in res]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uri", type=str, required=True)
    p.add_argument("--user", type=str, required=True)
    p.add_argument("--password", type=str, required=True)
    p.add_argument("--query", type=int, required=True, choices=[1, 2])
    p.add_argument("--user-id", type=str, default="")
    p.add_argument("--limit", type=int, default=10)
    args = p.parse_args()

    driver = _connect_driver_with_retry(args.uri, args.user, args.password)
    if args.query == 1:
        if not args.user_id:
            raise SystemExit("--user-id is required for query 1")
        out = q1_reachable_stations(driver, args.user_id)
    else:
        out = q2_top3_important_stations(driver)
    driver.close()

    print(f"rows={len(out)} showing first {min(args.limit, len(out))}")
    for r in out[: args.limit]:
        print(r)


if __name__ == "__main__":
    main()

