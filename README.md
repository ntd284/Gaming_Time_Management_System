# End-to-End Real-Time Gaming Time Management System

This project contains the design and implementation of an End-to-End Real-Time Gaming Time Management System. The system ensures compliance with the Gaming Restriction Law, which mandates:

- Users under 18 can play a single game for a maximum of 60 minutes per day.
- The total gaming time across all games must not exceed 120 minutes per day.

The architecture captures, processes, and exposes gaming session data via an API to enforce these rules in real-time, using: **Kafka, Spark, Cassandra,Redis** and **FastApi**.

![architecture](images/0_architecture.png)

## Main Requirements:
**Time Window**
- The playing time is calculated within a strict 24-hour window.
- The window starts at 12:00 AM and ends at 11:59 PM (UTC+7).
- At the beginning of each new day, the playing time resets automatically.
**Calculation Logic**
-   **Event Collection:**
    - User events are captured in real-time with minute-level granularity to ensure accuracy.
- **Online Time Calculation:**
    - The system calculates distinct active minutes per user across all games.
    - Duplicate or overlapping minutes are ignored to prevent inflated results.
    - Final playing time is the sum of unique active minutes within the time window.

## Getting Started

### Project files:

- [Fetch and produce events](plugins/produce_kafka.py): Fetches latest events from the API and produces them to the Consumer in message queue using **Kafka**.
- [Consume events](plugins/spark_streaming.py): Consumes events from the message queue, processes them with Spark Streaming, and stores raw data in **Cassandra** and processed data in **Redis** for real-time access.
- [FetchAPi](plugins/plugins/fetch_api.py): Clients want to capture, process, and expose gaming session data via an API to enforce the rules in real-time using **FastAPI**. 
- Reset per day: Using [cronjob](cronfile) and [flushdb](plugins/flushdb.py) Resets the gaming time for all user at the beginning of a new day at 00:00 AM