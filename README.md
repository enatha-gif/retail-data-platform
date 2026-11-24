# Online Retail Data Platform

## Project Overview

An end-to-end data engineering platform for an online retail company.

The project extracts data from a read-only Supabase PostgreSQL database, loads it into a local PostgreSQL data warehouse, and transforms it using dbt into an analytical star schema.

## Technologies

- Python
- PostgreSQL
- SQL
- dbt
- Git and GitHub

## Architecture

Supabase PostgreSQL
        |
        v
Python ETL Pipeline
        |
        v
PostgreSQL Staging Schema
        |
        v
dbt Transformations
        |
        v
Analytics Star Schema
        |
        v
Business Analysis

## Extraction Method

Python incremental extraction using updated_at.

## Project Status

Stage 1: Project setup.
