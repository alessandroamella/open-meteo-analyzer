#!/usr/bin/env python3

import json
from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta


def get_coordinates(place_name):
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": place_name, "count": 1, "language": "en", "format": "json"}
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    if "results" in data and data["results"]:
        return data["results"][0]
    return None


def fetch_weather_data(lat, lon, start_date, end_date, timezone="auto"):
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "daily": "temperature_2m_max,temperature_2m_min,temperature_2m_mean",
        "timezone": timezone,
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def parse_date_input(date_str, is_start=True):
    """
    Parse date input that can be:
    - YYYY (e.g., "2023")
    - YYYY-MM (e.g., "2023-05")
    - YYYY-MM-DD (e.g., "2023-05-15")

    For start dates: defaults to first day/month
    For end dates: defaults to last day/month, but clamped to yesterday at most
    """
    date_str = date_str.strip()
    yesterday = datetime.now() - relativedelta(days=1)

    if len(date_str) == 4:  # YYYY format
        try:
            year = int(date_str)
            if is_start:
                result_date = f"{year}-01-01"
            else:
                result_date = f"{year}-12-31"
                # Clamp end date to yesterday if it's in the future
                parsed_date = datetime.strptime(result_date, "%Y-%m-%d")
                if parsed_date > yesterday:
                    result_date = yesterday.strftime("%Y-%m-%d")
            return result_date
        except ValueError:
            raise ValueError("Invalid year format. Please use YYYY.")

    elif len(date_str) == 7 and date_str[4] == "-":  # YYYY-MM format
        try:
            year, month = date_str.split("-")
            year = int(year)
            month = int(month)

            if month < 1 or month > 12:
                raise ValueError("Month must be between 1 and 12.")

            if is_start:
                result_date = f"{year}-{month:02d}-01"
            else:
                # Get last day of the month
                if month == 12:
                    next_month_date = datetime(year + 1, 1, 1)
                else:
                    next_month_date = datetime(year, month + 1, 1)
                last_day = (next_month_date - relativedelta(days=1)).day
                result_date = f"{year}-{month:02d}-{last_day:02d}"
                # Clamp end date to yesterday if it's in the future
                parsed_date = datetime.strptime(result_date, "%Y-%m-%d")
                if parsed_date > yesterday:
                    result_date = yesterday.strftime("%Y-%m-%d")
            return result_date
        except ValueError:
            raise ValueError("Invalid year-month format. Please use YYYY-MM.")

    elif (
        len(date_str) == 10 and date_str[4] == "-" and date_str[7] == "-"
    ):  # YYYY-MM-DD format
        try:
            parsed_date = datetime.strptime(date_str, "%Y-%m-%d")
            if not is_start and parsed_date > yesterday:
                # Clamp end date to yesterday if it's in the future
                return yesterday.strftime("%Y-%m-%d")
            return date_str
        except ValueError:
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")

    else:
        raise ValueError(
            "Invalid date format. Please use YYYY, YYYY-MM, or YYYY-MM-DD."
        )


def main():
    place = input("🔎 Enter the name of the location: ").strip()
    location = get_coordinates(place)

    if not location:
        print("❌ Location not found. Try a different name.")
        return

    print(
        f"✅ Found: {location['name']}, {location.get('country', '')} (lat: {location['latitude']}, lon: {location['longitude']})"
    )

    start_date = input("📅 Enter start date (YYYY-MM-DD, YYYY-MM, or YYYY): ").strip()
    end_date = input("📅 Enter end date (YYYY-MM-DD, YYYY-MM, or YYYY): ").strip()

    # Validate and parse date format
    try:
        start_date = parse_date_input(start_date, is_start=True)
        end_date = parse_date_input(end_date, is_start=False)
    except ValueError as e:
        print(f"❌ {e}")
        return

    print(f"📥 Fetching data from {start_date} to {end_date}...")

    try:
        data = fetch_weather_data(
            location["latitude"], location["longitude"], start_date, end_date
        )
    except Exception as e:
        print(f"❌ Failed to fetch data: {e}")
        return

    # Add location metadata to the data
    enhanced_data = {
        "source": {
            "name": "Open-Meteo",
            "description": "Open-source weather API with historical weather data",
            "api_url": "https://archive-api.open-meteo.com/v1/archive",
            "geocoding_url": "https://geocoding-api.open-meteo.com/v1/search",
            "website": "https://open-meteo.com/",
            "license": "Open data with attribution required",
        },
        "location": {
            "name": location["name"],
            "country": location.get("country", ""),
            "latitude": location["latitude"],
            "longitude": location["longitude"],
        },
        "date_range": {"start_date": start_date, "end_date": end_date},
        "weather_data": data,
    }

    filename = f"{location['name'].replace(' ', '_')}_{start_date}_to_{end_date}.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(enhanced_data, f, indent=4)

    print(f"✅ Data saved to `{filename}`")


if __name__ == "__main__":
    main()
