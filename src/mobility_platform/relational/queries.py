from __future__ import annotations

import argparse
import sqlite3
from typing import Any, Dict, List


def q1_trips_with_user_and_station_names(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          t.trip_id,
          u.user_id, u.name, u.surname, u.birthdate, u.country,
          ss.name AS start_station_name,
          es.name AS end_station_name,
          t.start_time, t.end_time, t.cost
        FROM trips t
        JOIN users u ON u.user_id = t.user_id
        JOIN stations ss ON ss.station_id = t.start_station_id
        JOIN stations es ON es.station_id = t.end_station_id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def q2_users_with_trip_count_and_avg_duration(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          u.user_id, u.name, u.surname,
          COUNT(t.trip_id) AS trips_count,
          AVG((julianday(t.end_time) - julianday(t.start_time)) * 24.0 * 60.0) AS avg_duration_min
        FROM users u
        LEFT JOIN trips t ON t.user_id = u.user_id
        GROUP BY u.user_id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def q3_stations_with_start_end_trip_counts(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
          s.station_id, s.name, s.city,
          SUM(CASE WHEN t.start_station_id = s.station_id THEN 1 ELSE 0 END) AS trips_starting_here,
          SUM(CASE WHEN t.end_station_id = s.station_id THEN 1 ELSE 0 END) AS trips_ending_here
        FROM stations s
        LEFT JOIN trips t
          ON t.start_station_id = s.station_id OR t.end_station_id = s.station_id
        GROUP BY s.station_id
        """
    ).fetchall()
    return [dict(r) for r in rows]


def q4_trips_with_at_least_one_error_event(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT DISTINCT t.trip_id, t.user_id, t.start_time, t.end_time, t.cost
        FROM trips t
        JOIN events e ON e.trip_id = t.trip_id
        WHERE e.type = 'ERROR'
        """
    ).fetchall()
    return [dict(r) for r in rows]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--db", type=str, required=True, help="SQLite db path")
    p.add_argument("--query", type=int, required=True, choices=[1, 2, 3, 4])
    p.add_argument("--limit", type=int, default=5)
    args = p.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    if args.query == 1:
        out = q1_trips_with_user_and_station_names(conn)
    elif args.query == 2:
        out = q2_users_with_trip_count_and_avg_duration(conn)
    elif args.query == 3:
        out = q3_stations_with_start_end_trip_counts(conn)
    else:
        out = q4_trips_with_at_least_one_error_event(conn)

    print(f"rows={len(out)} showing first {min(args.limit, len(out))}")
    for r in out[: args.limit]:
        print(r)


if __name__ == "__main__":
    main()

