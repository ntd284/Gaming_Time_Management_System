# End-to-End Real-Time Gaming Time Management System

This project contains the design and implementation of an End-to-End Real-Time Gaming Time Management System. The system ensures compliance with the Gaming Restriction Law, which mandates:

- Users under 18 can play a single game for a maximum of 60 minutes per day.
- The total gaming time across all games must not exceed 120 minutes per day.

The architecture captures, processes, and exposes gaming session data via an API to enforce these rules in real-time, using: **Kafka, Spark, Cassandra,Redis** and **FastApi**.

![architecture](images/0_architecture.png)