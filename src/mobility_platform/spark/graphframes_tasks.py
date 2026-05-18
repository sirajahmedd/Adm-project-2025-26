from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import SparkSession, functions as F


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=str, required=True, help="Folder with trips.jsonl and stations.jsonl")
    args = p.parse_args()

    data_dir = Path(args.data)
    trips_path = str(data_dir / "trips.jsonl")
    stations_path = str(data_dir / "stations.jsonl")

    spark = SparkSession.builder.appName("mobility-graphframes").getOrCreate()

    # GraphFrames may require the package at runtime; see report/README for setup notes.
    try:
        from graphframes import GraphFrame  # type: ignore
    except Exception as e:
        raise SystemExit(
            "GraphFrames not available. Install GraphFrames compatible with your Spark version.\n"
            "For example, for Spark 3.5 you typically add the GraphFrames package via spark-submit --packages.\n"
            f"Original error: {e}"
        )

    trips = spark.read.json(trips_path)
    stations = spark.read.json(stations_path)

    # Build a STATION subgraph: edges between stations via trips (start -> end)
    v = stations.select(F.col("station_id").alias("id"), F.col("name"), F.col("city"))
    e = trips.select(F.col("start_station_id").alias("src"), F.col("end_station_id").alias("dst"))

    g = GraphFrame(v, e)

    # Task 1: top-3 important stations using PageRank
    pr = g.pageRank(resetProbability=0.15, maxIter=10)
    pr.vertices.orderBy(F.col("pagerank").desc()).show(3, truncate=False)

    # Task 2: connected components of the station subgraph
    cc = g.connectedComponents()
    cc.select("id", "component", "name", "city").orderBy("component").show(20, truncate=False)

    spark.stop()


if __name__ == "__main__":
    main()

