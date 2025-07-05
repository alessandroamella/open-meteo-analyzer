# Open-Meteo Weather Fetcher & Visualizer

This project includes two Python scripts to fetch and visualize historical weather data using the [Open-Meteo API](https://open-meteo.com/).

## Why

This is especially for those people who scream "iT's sUMmEr oF CoURSE iT's hOt" when the temperature has never been so high in the course of history.

It allows you to fetch historical temperature data and plot it to see trends over time, generating visualizations that can help understand climate patterns.

So maybe you can convince them that it is not just a "normal" summer (although, with some people, it might be a lost cause).

## Requirements

- Python 3.7+

- Libraries: `requests`, `python-dateutil`, `pandas`, `matplotlib`, `seaborn`

Install with:

```bash
pip install -r requirements.txt
```

## 1. Fetch Weather Data

`open_meteo_fetcher.py` fetches historical temperature data (min, max, mean) for a location and date range. Saves it to a JSON file.
Run:

You will be prompted for:

- Location name

- Start and end date (`YYYY`, `YYYY-MM`, or `YYYY-MM-DD`)

Example output file:

`Berlin_2023-01-01_to_2023-12-31.json`

## 2. Visualize Data

`visualization_openmeteo.py` generates a temperature trend chart from the saved JSON.
Usage:

Options:

- `--year YYYY`

- `--year-range START END`

- `--month MM`

- `--month-range START END`

Example:

Plots are saved to the `img/` directory.

## Data Source

- Open-Meteo Archive API: [https://archive-api.open-meteo.com](https://archive-api.open-meteo.com/)

- Geocoding API: [https://geocoding-api.open-meteo.com](https://geocoding-api.open-meteo.com/)

Open data license with attribution.
