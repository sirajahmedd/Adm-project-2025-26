from __future__ import annotations

import argparse
from pathlib import Path

from pyspark.sql import SparkSession, functions as F


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", type=str, required=True, help="Folder with trip_docs.jsonl")
    args = p.parse_args()

    data_dir = Path(args.data)
    trip_docs = str(data_dir / "trip_docs.jsonl")

    spark = (
        SparkSession.builder.appName("mobility-query2-users-stats")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )

    df = spark.read.json(trip_docs)
    df = df.withColumn("start_dt", F.to_timestamp("start_time")).withColumn("end_dt", F.to_timestamp("end_time"))
    df = df.withColumn("duration_min", (F.unix_timestamp("end_dt") - F.unix_timestamp("start_dt")) / 60.0)

    out = (
        df.groupBy(F.col("user.user_id").alias("user_id"), F.col("user.name").alias("name"), F.col("user.surname").alias("surname"))
        .agg(F.count("*").alias("trips_count"), F.avg("duration_min").alias("avg_duration_min"))
        .orderBy(F.col("trips_count").desc())
    )

    out.show(20, truncate=False)
    spark.stop()


if __name__ == "__main__":
    main()

