#!/usr/bin/env python3

import argparse
import json
import os

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pandas as pd
import seaborn as sns


def visualize_weather_data(
    filename, year=None, year_range=None, month=None, month_range=None
):
    if not os.path.exists(filename):
        print(f"❌ File '{filename}' not found.")
        return

    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract location and weather data from new structure
    location_info = data.get("location", {})
    location_name = location_info.get("name", "Unknown Location")
    location_country = location_info.get("country", "")
    location_display = (
        f"{location_name}, {location_country}" if location_country else location_name
    )

    # Extract source information
    source_info = data.get("source", {})
    source_name = source_info.get("name", "Unknown Source")

    # Extract coordinates for filename
    weather_data = data.get("weather_data", {})
    if not weather_data:
        print("❌ No weather data found in the file.")
        return

    latitude = weather_data.get("latitude", "")
    longitude = weather_data.get("longitude", "")
    location_coords = f"{latitude}_{longitude}"

    daily_data = weather_data.get("daily", {})
    if not daily_data:
        print("❌ No daily data found in the file.")
        return

    # Create DataFrame
    df = pd.DataFrame(
        {
            "date": daily_data.get("time", []),
            "temp_min": daily_data.get("temperature_2m_min", []),
            "temp_max": daily_data.get("temperature_2m_max", []),
            "temp_mean": daily_data.get("temperature_2m_mean", []),
        }
    )

    df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")
    df["year"] = df["date"].dt.year
    df["month"] = df["date"].dt.month

    # Apply filters
    df_filtered = df.copy()

    # Filter by year
    if year is not None:
        df_filtered = df_filtered[df_filtered["year"] == year]
        print(f"🔍 Filtering data for year: {year}")
    elif year_range is not None:
        start_year, end_year = year_range
        df_filtered = df_filtered[
            (df_filtered["year"] >= start_year) & (df_filtered["year"] <= end_year)
        ]
        print(f"🔍 Filtering data for years: {start_year}-{end_year}")

    # Filter by month
    if month is not None:
        df_filtered = df_filtered[df_filtered["month"] == month]
        month_name = (
            df_filtered["date"].dt.strftime("%B").iloc[0]
            if not df_filtered.empty
            else f"Month {month}"
        )
        print(f"🔍 Filtering data for month: {month_name}")
    elif month_range is not None:
        start_month, end_month = month_range
        if start_month <= end_month:
            # Same year range (e.g., March to August)
            df_filtered = df_filtered[
                (df_filtered["month"] >= start_month)
                & (df_filtered["month"] <= end_month)
            ]
        else:
            # Cross-year range (e.g., November to February)
            df_filtered = df_filtered[
                (df_filtered["month"] >= start_month)
                | (df_filtered["month"] <= end_month)
            ]
        print(f"🔍 Filtering data for months: {start_month}-{end_month}")

    # Remove rows with missing mean temp
    df_clean = df_filtered.dropna(subset=["temp_mean"])

    if df_clean.empty:
        print("⚠️ No usable temperature data found.")
        return

    # Compute yearly average
    yearly_stats = (
        df_clean.groupby("year")
        .agg({"temp_mean": "mean", "temp_min": "mean", "temp_max": "mean"})
        .reset_index()
    )

    # Plotting
    sns.set_theme(style="whitegrid", palette="muted")
    fig, ax = plt.subplots(figsize=(15, 8))

    # Fill range between min and max
    ax.fill_between(
        yearly_stats["year"],
        yearly_stats["temp_min"],
        yearly_stats["temp_max"],
        color="skyblue",
        alpha=0.3,
        label="Range tra Media Min/Max",
    )

    # Mean temp line
    ax.plot(
        yearly_stats["year"],
        yearly_stats["temp_mean"],
        color="royalblue",
        marker="o",
        label="Temperatura Media Annuale",
    )

    # Titles and labels
    title_suffix = ""
    if year is not None:
        title_suffix = f" - Anno {year}"
    elif year_range is not None:
        title_suffix = f" - Anni {year_range[0]}-{year_range[1]}"

    if month is not None:
        month_name = pd.to_datetime(f"2000-{month:02d}-01").strftime("%B")
        title_suffix += f" - {month_name}"
    elif month_range is not None:
        start_month_name = pd.to_datetime(f"2000-{month_range[0]:02d}-01").strftime(
            "%B"
        )
        end_month_name = pd.to_datetime(f"2000-{month_range[1]:02d}-01").strftime("%B")
        title_suffix += f" - {start_month_name} a {end_month_name}"

    ax.set_title(
        f"Temperature Medie - {location_display}{title_suffix}",
        fontsize=18,
        fontweight="bold",
        pad=20,
    )
    ax.set_xlabel("Anno", fontsize=12)
    ax.set_ylabel("Temperatura (°C)", fontsize=12)

    # X ticks
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.xticks(rotation=45)

    ax.legend(fontsize=12)
    ax.grid(True, linestyle="--", linewidth=0.5)

    # Add source information
    source_text = f"Fonte: {source_name}"
    if source_info.get("website"):
        source_text += f" ({source_info['website']})"

    plt.figtext(
        0.99,
        0.01,
        source_text,
        fontsize=8,
        ha="right",
        va="bottom",
        style="italic",
        alpha=0.7,
    )

    plt.tight_layout()

    # Save to file
    os.makedirs("img", exist_ok=True)
    filename_suffix = ""
    if year is not None:
        filename_suffix += f"_year{year}"
    elif year_range is not None:
        filename_suffix += f"_years{year_range[0]}-{year_range[1]}"
    if month is not None:
        filename_suffix += f"_month{month:02d}"
    elif month_range is not None:
        filename_suffix += f"_months{month_range[0]:02d}-{month_range[1]:02d}"

    output_file = f"img/weather_trend_{location_coords}{filename_suffix}.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")
    print(f"📈 Grafico salvato in: {output_file}")
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visualize weather data from Open-Meteo JSON files"
    )
    parser.add_argument(
        "filename", help="Path to the JSON file containing weather data"
    )
    parser.add_argument("--year", type=int, help="Filter data for a specific year")
    parser.add_argument(
        "--year-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Filter data for a year range (e.g., --year-range 2000 2010)",
    )
    parser.add_argument(
        "--month",
        type=int,
        choices=range(1, 13),
        metavar="MONTH",
        help="Filter data for a specific month (1-12)",
    )
    parser.add_argument(
        "--month-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Filter data for a month range (e.g., --month-range 6 8 for June to August)",
    )

    args = parser.parse_args()

    # Validate arguments
    if args.year and args.year_range:
        print("❌ Cannot specify both --year and --year-range")
        exit(1)

    if args.month and args.month_range:
        print("❌ Cannot specify both --month and --month-range")
        exit(1)

    if args.month_range:
        start_month, end_month = args.month_range
        if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
            print("❌ Month range values must be between 1 and 12")
            exit(1)

    if args.year_range:
        start_year, end_year = args.year_range
        if start_year > end_year:
            print("❌ Start year must be less than or equal to end year")
            exit(1)

    # Convert to tuples for easier handling
    year_range = tuple(args.year_range) if args.year_range else None
    month_range = tuple(args.month_range) if args.month_range else None

    visualize_weather_data(
        args.filename,
        year=args.year,
        year_range=year_range,
        month=args.month,
        month_range=month_range,
    )
