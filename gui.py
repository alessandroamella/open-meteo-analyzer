#!/usr/bin/env python3
"""
Open-Meteo Weather Data GUI
A graphical interface for fetching and visualizing weather data using the Open-Meteo API
"""

import json
import os
import subprocess
import threading
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import filedialog, messagebox, ttk


class WeatherDataGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Open-Meteo Weather Data Analyzer")
        self.root.geometry("800x700")

        # Script paths (assuming they're in the same directory)
        self.fetcher_script = "./fetcher.py"
        self.visualization_script = "./visualizer.py"

        # Variables
        self.location_data = {}
        self.weather_data_file = None

        self.setup_ui()

    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Open-Meteo Weather Data Analyzer",
            font=("Arial", 16, "bold"),
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        # Location Section
        location_frame = ttk.LabelFrame(main_frame, text="Location", padding="10")
        location_frame.grid(
            row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        location_frame.columnconfigure(1, weight=1)

        ttk.Label(location_frame, text="Location:").grid(row=0, column=0, sticky=tk.W)
        self.location_entry = ttk.Entry(location_frame, width=30)
        self.location_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))

        self.check_location_btn = ttk.Button(
            location_frame, text="Check Location", command=self.check_location
        )
        self.check_location_btn.grid(row=0, column=2, padx=(5, 0))

        # Location info display
        self.location_info = ttk.Label(location_frame, text="", foreground="green")
        self.location_info.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(5, 0))

        # Date Range Section
        date_frame = ttk.LabelFrame(main_frame, text="Date Range", padding="10")
        date_frame.grid(
            row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        date_frame.columnconfigure(1, weight=1)
        date_frame.columnconfigure(3, weight=1)

        # Start date
        ttk.Label(date_frame, text="Start Date:").grid(row=0, column=0, sticky=tk.W)
        self.start_date_entry = ttk.Entry(date_frame, width=15)
        self.start_date_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
        self.start_date_entry.insert(0, "2023-01-01")

        # End date
        ttk.Label(date_frame, text="End Date:").grid(row=0, column=2, sticky=tk.W)
        self.end_date_entry = ttk.Entry(date_frame, width=15)
        self.end_date_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(5, 0))
        self.end_date_entry.insert(0, "2023-12-31")

        # Date format help
        date_help = ttk.Label(
            date_frame,
            text="Format: YYYY-MM-DD, YYYY-MM, or YYYY",
            font=("Arial", 8),
            foreground="gray",
        )
        date_help.grid(row=1, column=0, columnspan=4, sticky=tk.W, pady=(5, 0))

        # Quick date selections
        quick_date_frame = ttk.Frame(date_frame)
        quick_date_frame.grid(
            row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=(10, 0)
        )

        ttk.Button(quick_date_frame, text="Last Year", command=self.set_last_year).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(quick_date_frame, text="This Year", command=self.set_this_year).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(
            quick_date_frame, text="Last 30 Days", command=self.set_last_30_days
        ).pack(side=tk.LEFT, padx=(0, 5))

        # Filter Options Section
        filter_frame = ttk.LabelFrame(main_frame, text="Filter Options", padding="10")
        filter_frame.grid(
            row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10)
        )
        filter_frame.columnconfigure(1, weight=1)
        filter_frame.columnconfigure(3, weight=1)

        # Year filter
        self.year_filter_var = tk.BooleanVar()
        self.year_filter_check = ttk.Checkbutton(
            filter_frame,
            text="Filter by year:",
            variable=self.year_filter_var,
            command=self.toggle_year_filter,
        )
        self.year_filter_check.grid(row=0, column=0, sticky=tk.W)

        self.year_entry = ttk.Entry(filter_frame, width=10, state="disabled")
        self.year_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 10))

        # Month filter
        self.month_filter_var = tk.BooleanVar()
        self.month_filter_check = ttk.Checkbutton(
            filter_frame,
            text="Filter by month:",
            variable=self.month_filter_var,
            command=self.toggle_month_filter,
        )
        self.month_filter_check.grid(row=0, column=2, sticky=tk.W)

        self.month_combo = ttk.Combobox(filter_frame, width=10, state="disabled")
        self.month_combo["values"] = (
            "1 - January",
            "2 - February",
            "3 - March",
            "4 - April",
            "5 - May",
            "6 - June",
            "7 - July",
            "8 - August",
            "9 - September",
            "10 - October",
            "11 - November",
            "12 - December",
        )
        self.month_combo.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))

        # Visualization Options Section
        viz_frame = ttk.LabelFrame(
            main_frame, text="Visualization Options", padding="10"
        )
        viz_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))

        # Options checkboxes
        options_frame = ttk.Frame(viz_frame)
        options_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

        self.dark_theme_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="Dark theme", variable=self.dark_theme_var
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.trend_line_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="Show trend line", variable=self.trend_line_var
        ).pack(side=tk.LEFT, padx=(0, 15))

        self.no_display_var = tk.BooleanVar()
        ttk.Checkbutton(
            options_frame, text="Save only (no display)", variable=self.no_display_var
        ).pack(side=tk.LEFT)

        # Output file option
        output_frame = ttk.Frame(viz_frame)
        output_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        output_frame.columnconfigure(1, weight=1)

        ttk.Label(output_frame, text="Output file (optional):").grid(
            row=0, column=0, sticky=tk.W
        )
        self.output_entry = ttk.Entry(output_frame)
        self.output_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 5))

        ttk.Button(output_frame, text="Browse", command=self.browse_output_file).grid(
            row=0, column=2
        )

        # Action Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=3, pady=(20, 0))

        self.fetch_btn = ttk.Button(
            button_frame,
            text="Fetch Weather Data",
            command=self.fetch_weather_data,
            style="Accent.TButton",
        )
        self.fetch_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.visualize_btn = ttk.Button(
            button_frame,
            text="Visualize Data",
            command=self.visualize_data,
            state="disabled",
        )
        self.visualize_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.fetch_and_visualize_btn = ttk.Button(
            button_frame, text="Fetch & Visualize", command=self.fetch_and_visualize
        )
        self.fetch_and_visualize_btn.pack(side=tk.LEFT)

        # Status Section
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(
            row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0)
        )
        status_frame.columnconfigure(0, weight=1)

        self.status_text = tk.Text(status_frame, height=8, width=80)
        self.status_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Scrollbar for status text
        scrollbar = ttk.Scrollbar(
            status_frame, orient="vertical", command=self.status_text.yview
        )
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.status_text.configure(yscrollcommand=scrollbar.set)

        status_frame.rowconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

    def log_status(self, message):
        """Add a message to the status text with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.status_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.status_text.see(tk.END)
        self.root.update_idletasks()

    def check_location(self):
        """Check if the location is valid using the fetcher script"""
        location = self.location_entry.get().strip()
        if not location:
            messagebox.showerror("Error", "Please enter a location name")
            return

        self.log_status(f"Checking location: {location}")
        self.check_location_btn.config(state="disabled")

        def run_check():
            try:
                # Run the location check command
                cmd = [self.fetcher_script, "--check-location", location]
                subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Try to find the JSON output file
                # The script typically saves to {location_name}_location.json
                location_filename = (
                    location.lower().replace(" ", "_") + "_location.json"
                )

                if os.path.exists(location_filename):
                    with open(location_filename, "r") as f:
                        self.location_data = json.load(f)

                    if self.location_data.get("results"):
                        location_info = self.location_data["results"][0]
                        info_text = f"✓ Found: {location_info['name']}, {location_info.get('country', 'Unknown')} ({location_info['latitude']:.4f}, {location_info['longitude']:.4f})"
                        self.location_info.config(text=info_text, foreground="green")
                        self.log_status(f"Location verified: {info_text}")
                    else:
                        self.location_info.config(
                            text="✗ Location not found", foreground="red"
                        )
                        self.log_status("Location not found")
                else:
                    self.location_info.config(
                        text="✓ Location check completed", foreground="green"
                    )
                    self.log_status("Location check completed")

            except subprocess.CalledProcessError as e:
                error_msg = f"Error checking location: {e.stderr}"
                self.location_info.config(
                    text="✗ Error checking location", foreground="red"
                )
                self.log_status(error_msg)
                messagebox.showerror("Location Check Error", error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.location_info.config(
                    text="✗ Error checking location", foreground="red"
                )
                self.log_status(error_msg)
                messagebox.showerror("Error", error_msg)
            finally:
                self.check_location_btn.config(state="normal")

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=run_check)
        thread.daemon = True
        thread.start()

    def toggle_year_filter(self):
        """Toggle year filter entry state"""
        if self.year_filter_var.get():
            self.year_entry.config(state="normal")
        else:
            self.year_entry.config(state="disabled")

    def toggle_month_filter(self):
        """Toggle month filter combo state"""
        if self.month_filter_var.get():
            self.month_combo.config(state="readonly")
        else:
            self.month_combo.config(state="disabled")

    def set_last_year(self):
        """Set dates to last year"""
        last_year = datetime.now().year - 1
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, f"{last_year}-01-01")
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, f"{last_year}-12-31")

    def set_this_year(self):
        """Set dates to this year"""
        this_year = datetime.now().year
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, f"{this_year}-01-01")
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, f"{this_year}-12-31")

    def set_last_30_days(self):
        """Set dates to last 30 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        self.start_date_entry.delete(0, tk.END)
        self.start_date_entry.insert(0, start_date.strftime("%Y-%m-%d"))
        self.end_date_entry.delete(0, tk.END)
        self.end_date_entry.insert(0, end_date.strftime("%Y-%m-%d"))

    def browse_output_file(self):
        """Browse for output file location"""
        filename = filedialog.asksaveasfilename(
            title="Save chart as",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
        )
        if filename:
            # Remove extension as the script adds it
            filename = os.path.splitext(filename)[0]
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, filename)

    def fetch_weather_data(self):
        """Fetch weather data using the fetcher script"""
        location = self.location_entry.get().strip()
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()

        if not location or not start_date or not end_date:
            messagebox.showerror("Error", "Please fill in location and date range")
            return

        self.log_status(
            f"Fetching weather data for {location} from {start_date} to {end_date}"
        )
        self.fetch_btn.config(state="disabled")

        def run_fetch():
            try:
                # Build command
                cmd = [
                    self.fetcher_script,
                    "--location",
                    location,
                    "--start-date",
                    start_date,
                    "--end-date",
                    end_date,
                ]

                # Run the fetch command
                subprocess.run(cmd, capture_output=True, text=True, check=True)

                # Find the generated weather data file
                # The script typically saves to {location_name}_weather_data.json
                weather_filename = (
                    location.lower().replace(" ", "_") + "_weather_data.json"
                )

                if os.path.exists(weather_filename):
                    self.weather_data_file = weather_filename
                    self.visualize_btn.config(state="normal")
                    self.log_status(f"Weather data saved to: {weather_filename}")
                    self.log_status("Weather data fetching completed successfully!")
                else:
                    self.log_status("Weather data file not found after fetching")

            except subprocess.CalledProcessError as e:
                error_msg = f"Error fetching weather data: {e.stderr}"
                self.log_status(error_msg)
                messagebox.showerror("Fetch Error", error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.log_status(error_msg)
                messagebox.showerror("Error", error_msg)
            finally:
                self.fetch_btn.config(state="normal")

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=run_fetch)
        thread.daemon = True
        thread.start()

    def visualize_data(self):
        """Visualize the weather data using the visualization script"""
        if not self.weather_data_file or not os.path.exists(self.weather_data_file):
            messagebox.showerror(
                "Error", "No weather data file found. Please fetch data first."
            )
            return

        self.log_status(f"Visualizing data from: {self.weather_data_file}")
        self.visualize_btn.config(state="disabled")

        def run_visualization():
            try:
                # Build command
                cmd = [self.visualization_script, self.weather_data_file]

                # Add filters
                if self.year_filter_var.get() and self.year_entry.get().strip():
                    cmd.extend(["--year", self.year_entry.get().strip()])

                if self.month_filter_var.get() and self.month_combo.get():
                    month_num = self.month_combo.get().split()[0]
                    cmd.extend(["--month", month_num])

                # Add visualization options
                if self.dark_theme_var.get():
                    cmd.append("--dark")

                if self.trend_line_var.get():
                    cmd.append("--trend")

                if self.no_display_var.get():
                    cmd.append("--no-display")

                if self.output_entry.get().strip():
                    cmd.extend(["--output", self.output_entry.get().strip()])

                # Run the visualization command
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)

                self.log_status("Visualization completed successfully!")
                if result.stdout:
                    self.log_status(f"Output: {result.stdout}")

            except subprocess.CalledProcessError as e:
                error_msg = f"Error creating visualization: {e.stderr}"
                self.log_status(error_msg)
                messagebox.showerror("Visualization Error", error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.log_status(error_msg)
                messagebox.showerror("Error", error_msg)
            finally:
                self.visualize_btn.config(state="normal")

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=run_visualization)
        thread.daemon = True
        thread.start()

    def fetch_and_visualize(self):
        """Fetch weather data and then visualize it"""
        location = self.location_entry.get().strip()
        start_date = self.start_date_entry.get().strip()
        end_date = self.end_date_entry.get().strip()

        if not location or not start_date or not end_date:
            messagebox.showerror("Error", "Please fill in location and date range")
            return

        self.log_status("Starting fetch and visualize process...")
        self.fetch_and_visualize_btn.config(state="disabled")

        def run_fetch_and_visualize():
            try:
                # First fetch the data
                self.log_status(
                    f"Fetching weather data for {location} from {start_date} to {end_date}"
                )

                fetch_cmd = [
                    self.fetcher_script,
                    "--location",
                    location,
                    "--start-date",
                    start_date,
                    "--end-date",
                    end_date,
                ]

                subprocess.run(fetch_cmd, capture_output=True, text=True, check=True)

                # Find the generated weather data file
                weather_filename = (
                    location.lower().replace(" ", "_") + "_weather_data.json"
                )

                if not os.path.exists(weather_filename):
                    raise Exception("Weather data file not found after fetching")

                self.weather_data_file = weather_filename
                self.log_status(f"Weather data saved to: {weather_filename}")

                # Now visualize the data
                self.log_status("Creating visualization...")

                viz_cmd = [self.visualization_script, weather_filename]

                # Add filters
                if self.year_filter_var.get() and self.year_entry.get().strip():
                    viz_cmd.extend(["--year", self.year_entry.get().strip()])

                if self.month_filter_var.get() and self.month_combo.get():
                    month_num = self.month_combo.get().split()[0]
                    viz_cmd.extend(["--month", month_num])

                # Add visualization options
                if self.dark_theme_var.get():
                    viz_cmd.append("--dark")

                if self.trend_line_var.get():
                    viz_cmd.append("--trend")

                if self.no_display_var.get():
                    viz_cmd.append("--no-display")

                if self.output_entry.get().strip():
                    viz_cmd.extend(["--output", self.output_entry.get().strip()])

                subprocess.run(viz_cmd, capture_output=True, text=True, check=True)

                self.visualize_btn.config(state="normal")
                self.log_status("Fetch and visualize completed successfully!")

            except subprocess.CalledProcessError as e:
                error_msg = f"Error in fetch and visualize: {e.stderr}"
                self.log_status(error_msg)
                messagebox.showerror("Process Error", error_msg)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                self.log_status(error_msg)
                messagebox.showerror("Error", error_msg)
            finally:
                self.fetch_and_visualize_btn.config(state="normal")

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=run_fetch_and_visualize)
        thread.daemon = True
        thread.start()


def main():
    root = tk.Tk()
    WeatherDataGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
