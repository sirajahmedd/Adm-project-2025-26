from __future__ import annotations

import argparse
from typing import Any, Dict, List

from pymongo import MongoClient


def q1_trips_with_user_and_station_names(trips_col) -> List[Dict[str, Any]]:
    pipeline = [
        {
            "$project": {
                "_id": 0,
                "trip_id": 1,
                "user": 1,
                "start_station_name": "$start_station.name",
                "end_station_name": "$end_station.name",
                "start_time": 1,
                "end_time": 1,
                "cost": 1,
            }
        }
    ]
    return list(trips_col.aggregate(pipeline))


def q2_users_with_trip_count_and_avg_duration(trips_col) -> List[Dict[str, Any]]:
    # Duration in minutes; times are ISO strings, converted to dates
    pipeline = [
        {
            "$addFields": {
                "start_dt": {"$dateFromString": {"dateString": "$start_time"}},
                "end_dt": {"$dateFromString": {"dateString": "$end_time"}},
            }
        },
        {
            "$addFields": {
                "duration_min": {
                    "$divide": [{"$subtract": ["$end_dt", "$start_dt"]}, 1000 * 60]
                }
            }
        },
        {
            "$group": {
                "_id": "$user.user_id",
                "name": {"$first": "$user.name"},
                "surname": {"$first": "$user.surname"},
                "trips_count": {"$sum": 1},
                "avg_duration_min": {"$avg": "$duration_min"},
            }
        },
        {"$project": {"_id": 0, "user_id": "$_id", "name": 1, "surname": 1, "trips_count": 1, "avg_duration_min": 1}},
    ]
    return list(trips_col.aggregate(pipeline))


def q3_stations_with_start_end_trip_counts(trips_col) -> List[Dict[str, Any]]:
    pipeline = [
        {
            "$facet": {
                "starts": [
                    {
                        "$group": {
                            "_id": "$start_station.station_id",
                            "station_name": {"$first": "$start_station.name"},
                            "city": {"$first": "$start_station.city"},
                            "trips_starting_here": {"$sum": 1},
                        }
                    }
                ],
                "ends": [
                    {
                        "$group": {
                            "_id": "$end_station.station_id",
                            "trips_ending_here": {"$sum": 1},
                        }
                    }
                ],
            }
        },
        {"$project": {"merged": {"$concatArrays": ["$starts", "$ends"]}}},
        {"$unwind": "$merged"},
        {"$replaceRoot": {"newRoot": "$merged"}},
        {
            "$group": {
                "_id": "$_id",
                "station_id": {"$first": "$_id"},
                "name": {"$max": "$station_name"},
                "city": {"$max": "$city"},
                "trips_starting_here": {"$max": "$trips_starting_here"},
                "trips_ending_here": {"$max": "$trips_ending_here"},
            }
        },
        {"$project": {"_id": 0}},
    ]
    return list(trips_col.aggregate(pipeline))


def q4_trips_with_at_least_one_error_event(trips_col) -> List[Dict[str, Any]]:
    pipeline = [
        {"$match": {"events.type": "ERROR"}},
        {"$project": {"_id": 0, "trip_id": 1, "user_id": "$user.user_id", "start_time": 1, "end_time": 1, "cost": 1}},
    ]
    return list(trips_col.aggregate(pipeline))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--uri", type=str, required=True)
    p.add_argument("--db", type=str, required=True)
    p.add_argument("--query", type=int, required=True, choices=[1, 2, 3, 4])
    p.add_argument("--limit", type=int, default=5)
    args = p.parse_args()

    client = MongoClient(args.uri)
    trips_col = client[args.db]["trips"]

    if args.query == 1:
        out = q1_trips_with_user_and_station_names(trips_col)
    elif args.query == 2:
        out = q2_users_with_trip_count_and_avg_duration(trips_col)
    elif args.query == 3:
        out = q3_stations_with_start_end_trip_counts(trips_col)
    else:
        out = q4_trips_with_at_least_one_error_event(trips_col)

    print(f"rows={len(out)} showing first {min(args.limit, len(out))}")
    for r in out[: args.limit]:
        print(r)


if __name__ == "__main__":
    main()

