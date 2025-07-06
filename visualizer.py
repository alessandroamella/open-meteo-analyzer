#!/usr/bin/env python3

import argparse
import json
import os
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
import seaborn as sns


def visualize_weather_data(
    filename,
    year=None,
    year_range=None,
    month=None,
    month_range=None,
    dark_theme=False,
    show_trend=False,
    output_filename=None,
    no_display=False,
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

    # Get current date for filtering
    current_date = datetime.now()
    current_year = current_date.year
    current_month = current_date.month

    # Apply filters
    df_filtered = df.copy()

    # Filter by year
    if year is not None:
        if year >= current_year:
            year = min(year, current_year - 1)
        df_filtered = df_filtered[df_filtered["year"] == year]
        print(f"🔍 Filtering data for year: {year}")
    elif year_range is not None:
        start_year, end_year = year_range
        if end_year >= current_year:
            end_year = min(end_year, current_year - 1)
        if start_year >= current_year:
            print(
                f"❌ No data available: start year {start_year} is current year or later"
            )
            return
        df_filtered = df_filtered[
            (df_filtered["year"] >= start_year) & (df_filtered["year"] <= end_year)
        ]
        print(f"🔍 Filtering data for years: {start_year}-{end_year}")
    else:
        # If no year filter specified, exclude current year
        df_filtered = df_filtered[df_filtered["year"] < current_year]

    # Filter by month
    if month is not None:
        # Exclude current and future months for the current year
        df_filtered = df_filtered[
            ~(
                (df_filtered["year"] == current_year)
                & (df_filtered["month"] >= current_month)
            )
        ]
        df_filtered = df_filtered[df_filtered["month"] == month]
        month_name = (
            df_filtered["date"].dt.strftime("%B").iloc[0]
            if not df_filtered.empty
            else f"Month {month}"
        )
        print(f"🔍 Filtering data for month: {month_name}")
    elif month_range is not None:
        start_month, end_month = month_range
        # Exclude current and future months for the current year
        df_filtered = df_filtered[
            ~(
                (df_filtered["year"] == current_year)
                & (df_filtered["month"] >= current_month)
            )
        ]
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
    else:
        # If no month filter specified, exclude current and future months for current year
        df_filtered = df_filtered[
            ~(
                (df_filtered["year"] == current_year)
                & (df_filtered["month"] >= current_month)
            )
        ]

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
    if dark_theme:
        print("🌙 Using dark theme")
        plt.style.use("dark_background")
        sns.set_theme(style="darkgrid", palette="bright")
        fig, ax = plt.subplots(figsize=(15, 8))
        # Set dark background colors explicitly
        fig.patch.set_facecolor("black")
        ax.set_facecolor("black")
    else:
        sns.set_theme(style="whitegrid", palette="muted")
        fig, ax = plt.subplots(figsize=(15, 8))

    # Fill range between min and max
    if dark_theme:
        fill_color = "steelblue"
        line_color = "cyan"
        grid_color = "gray"
    else:
        fill_color = "skyblue"
        line_color = "royalblue"
        grid_color = None

    ax.fill_between(
        yearly_stats["year"],
        yearly_stats["temp_min"],
        yearly_stats["temp_max"],
        color=fill_color,
        alpha=0.3,
        label="Range tra Media Min/Max",
    )

    # Mean temp line
    ax.plot(
        yearly_stats["year"],
        yearly_stats["temp_mean"],
        color=line_color,
        marker="o",
        label="Temperatura Media Annuale",
    )

    # Add trend line if requested
    if show_trend:
        years = yearly_stats["year"].values
        temps = yearly_stats["temp_mean"].values

        # Calculate linear regression
        coeffs = np.polyfit(years, temps, 1)
        trend_line = np.poly1d(coeffs)

        trend_color = "orange" if dark_theme else "red"
        ax.plot(
            years,
            trend_line(years),
            color=trend_color,
            linestyle="--",
            linewidth=2,
            label="Trend (Regressione Lineare)",
        )

        # Add start and end points on the trend line
        start_year = years[0]
        end_year = years[-1]
        start_temp = trend_line(start_year)
        end_temp = trend_line(end_year)

        # Plot trend start and end points
        ax.plot(
            [start_year, end_year],
            [start_temp, end_temp],
            color=trend_color,
            marker="s",
            markersize=8,
            linestyle="None",
            markeredgecolor="white" if dark_theme else "black",
            markeredgewidth=1,
            alpha=0.8,
        )

        # Add temperature annotations at start and end points
        ax.annotate(
            f"{start_temp:.1f}°C",
            (start_year, start_temp),
            xytext=(-6, -3.5),
            textcoords="offset points",
            fontsize=9,
            color=trend_color,
            weight="bold",
            ha="right",
        )

        ax.annotate(
            f"{end_temp:.1f}°C",
            (end_year, end_temp),
            xytext=(6, -3.5),
            textcoords="offset points",
            fontsize=9,
            color=trend_color,
            weight="bold",
            ha="left",
        )

        print(f"📊 Trend lineare: {coeffs[0]:.3f}°C per anno")
        print(f"📍 Temperatura trend inizio ({start_year}): {start_temp:.1f}°C")
        print(f"📍 Temperatura trend fine ({end_year}): {end_temp:.1f}°C")

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
        color="white" if dark_theme else "black",
    )
    ax.set_xlabel("Anno", fontsize=12, color="white" if dark_theme else "black")
    ax.set_ylabel(
        "Temperatura (°C)", fontsize=12, color="white" if dark_theme else "black"
    )

    # X ticks
    ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    plt.xticks(rotation=45)

    # Set tick colors for dark theme
    if dark_theme:
        ax.tick_params(colors="white")

    ax.legend(fontsize=12)
    grid_kwargs = {"linestyle": "--", "linewidth": 0.5}
    if grid_color:
        grid_kwargs["color"] = grid_color
    ax.grid(True, **grid_kwargs)

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

    if output_filename:
        # Use custom filename
        output_file = output_filename
        # Ensure the custom filename has .png extension
        if not output_file.endswith(".png"):
            output_file += ".png"
        # Add img/ directory if just filename is provided
        if "/" not in output_file:
            output_file = f"img/{output_file}"
    else:
        # Use default filename pattern
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

    if not no_display:
        plt.show()
    else:
        print("📄 Grafico non visualizzato (--no-display attivo)")
        plt.close()  # Close the figure to free memory


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Visualize weather data from Open-Meteo JSON files"
    )
    parser.add_argument(
        "filename", help="Path to the JSON file containing weather data"
    )
    parser.add_argument(
        "-y", "--year", type=int, help="Filter data for a specific year"
    )
    parser.add_argument(
        "-yr",
        "--year-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Filter data for a year range (e.g., --year-range 2000 2010)",
    )
    parser.add_argument(
        "-m",
        "--month",
        type=int,
        choices=range(1, 13),
        metavar="MONTH",
        help="Filter data for a specific month (1-12)",
    )
    parser.add_argument(
        "-mr",
        "--month-range",
        nargs=2,
        type=int,
        metavar=("START", "END"),
        help="Filter data for a month range (e.g., --month-range 6 8 for June to August)",
    )
    parser.add_argument(
        "-d",
        "--dark",
        action="store_true",
        help="Use dark theme for the visualization",
    )
    parser.add_argument(
        "-t",
        "--trend",
        action="store_true",
        help="Show linear trend line on the chart",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Custom filename for the output chart (default: auto-generated based on filters)",
    )
    parser.add_argument(
        "-n",
        "--no-display",
        action="store_true",
        help="Save chart without displaying it",
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
        dark_theme=args.dark,
        show_trend=args.trend,
        output_filename=args.output,
        no_display=args.no_display,
    )
