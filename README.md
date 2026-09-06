# ASG Airlines — End-to-End Data Engineering

## Project Overview

This project implements an end-to-end data engineering pipeline for ASG Airlines using flight, booking, passenger, and payment data.

The pipeline ingests data from Excel, performs data quality checks and transformations using Python and Pandas, stores the cleaned data in MySQL, creates analytical SQL views, and presents key operational insights through Power BI.

## Architecture

Excel → Python/Pandas → Data Quality & Transformation → MySQL → SQL Analytical Views → Power BI

## Project Structure

```text
Airlines_Project/
├── data/
│   └── raw/
├── notebooks/
├── src/
├── sql/
├── outputs/
│   ├── cleaned/
│   └── quarantine/
├── docs/
├── README.md
└── requirements.txt