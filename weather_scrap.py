# -*- coding: utf-8 -*-
# Based on https://bojanstavrikj.github.io/content/page1/wunderground_scraper
import csv
import os
import time

from argparse import ArgumentParser
from contextlib import contextmanager
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

from util import (
    farenheit_to_celcius,
    mph_to_kph,
    inch_to_mm,
    valid_date_format,
    fix_all_wrong_date,
    get_meridiem,
    dt_from_str,
    dt_to_str,
    progress_bar,
    COLUMNS
)

if os.name == "nt":
    from selenium.webdriver.edge.options import Options
    from selenium.webdriver.edge.service import Service
    from selenium.webdriver import Edge as Driver
    DRIVER_NAME = "msedgedriver.exe"
else:  # Linux
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver import Chrome as Driver
    DRIVER_NAME = "chromedriver"


@contextmanager
def initialize_driver(headless=True):
    print("[+] Initializing driver... ", end="", flush=True)
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    if os.name == "nt":
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
    driver = Driver(
        service=Service(executable_path=os.path.join(os.getcwd(), "drivers", DRIVER_NAME)),
        options=options
    )
    print("Done.")
    yield driver
    print("[+] Closing driver... ", end="", flush=True)
    driver.quit()
    print("Done.")


def resolve_station(driver: Driver, location: str):
    print("[+] Resolving Station... ", end="", flush=True)
    driver.get(f"https://www.wunderground.com/weather/be/{location}")
    while "city-almanac" not in driver.page_source:  # Wait for page to load
        time.sleep(0.1)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    print(f"Done.")

    return soup.find(class_="city-almanac").find(class_="module-header").find(string=True, recursive=False).strip()


def parse_command_line(custom_args=None):
    parser = ArgumentParser(description="Scrape weather data from 'wunderground.com'")
    parser.add_argument("-s", "--start", help="Start date (YYYY-MM-DD)", required=True)
    parser.add_argument("-e", "--end", help="End date (YYYY-MM-DD) included. Default is now.", default=None)
    parser.add_argument(
        "-d",
        "--days",
        help="Number of days to scrap. (Should be used instead of end date)",
        type=int, default=-1
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Output file name. Default: '<location_start_end>.csv'.",
        default="<location_start_end>.csv"
    )
    parser.add_argument("location", help="Location.")

    args = parser.parse_args(custom_args)

    valid_date_format(args.start, "start")
    args.start = dt_from_str(args.start, fmt="%Y-%m-%d")

    if args.end is None:
        args.end = args.start + timedelta(days=args.days - 1) if args.days > 0 else datetime.now()  # -1 because end date is included
    elif args.days > 0:
        exit("[!] You cannot use both end date and number of days.")
    else:
        valid_date_format(args.end, "end")
        args.end = dt_from_str(args.end, fmt="%Y-%m-%d")

    if args.start > args.end:
        exit("[!] Start date cannot be after end date.")

    if args.output == "<location_start_end>.csv":
        args.output = f"{args.location}_{dt_to_str(args.start, '%Y-%m-%d')}_{dt_to_str(args.end, '%Y-%m-%d')}.csv"
        print(f"[+] Using output '{args.output}'.")
    elif "." not in args.output:
        args.output += ".csv"

    return args


def day_scraper(page, date):
    soup = BeautifulSoup(page, "html.parser")
    rows = soup.find_all("tr", {"class": "mat-row cdk-row ng-star-inserted"})
    day_data = []
    for row in rows:
        columns = row.find_all("td", {"role": "gridcell"})

        wu, ng = {"class": "wu-value wu-value-to"}, {"class": "ng-star-inserted"}
        time_data = dict()

        time, ampm = columns[0].find("span", attrs=ng).text.split(" ")
        hour, minute = [int(x) for x in time.split(":")]
        hour = 0 if hour == 12 else hour
        hour += 12 if ampm == "PM" else 0

        time_data["date"] = date
        time_data["time"] = f"{hour}:{minute}:00"
        time_data["temperature"] = farenheit_to_celcius(columns[1].find("span", attrs=wu).text)
        time_data["dew_point"] = farenheit_to_celcius(columns[2].find("span", attrs=wu).text)
        time_data["humidity"] = int(columns[3].find("span", attrs=wu).text)
        time_data["wind"] = columns[4].find("span", attrs=ng).text
        time_data["wind_speed"] = mph_to_kph(columns[5].find("span", attrs=wu).text)
        time_data["wind_gust"] = mph_to_kph(columns[6].find("span", attrs=wu).text)
        time_data["pressure"] = float(columns[7].find("span", attrs=wu).text)
        time_data["precipitation"] = inch_to_mm(columns[8].find("span", attrs=wu).text)
        time_data["condition"] = columns[9].find("span", attrs=ng).text
        day_data.append(time_data)
    return day_data


if __name__ == "__main__":
    args = parse_command_line()

    time_start = time.time()
    if os.path.exists(args.output):
        while True:
            user_input = input(f"[!] File '{args.output}' already exists. Overwrite, Append or Stop ? [o/a/s] ")
            if user_input in ["o", "a", "s"]:
                break
        if user_input == "o":
            with open(args.output, "w", newline="") as file:
                csv.DictWriter(file, COLUMNS).writeheader()
        elif user_input == "a":
            pass  # We don't exit nor rewrite the file from scratch
        elif user_input == "s":
            exit("[!] Exiting...")
        else:
            exit("Mhmm... Weird.")

    BASE_URL = "https://www.wunderground.com/history/daily/be/{location}/{station}/date/{date}"

    with initialize_driver() as driver:
        station = resolve_station(driver=driver, location=args.location)

        days_count = 0
        days_total = (args.end - args.start).days + 1  # +1 include end date
        date_start = args.start

        while date_start <= args.end:
            date = dt_to_str(date_start, fmt="%Y-%m-%d")
            progress_bar(days_count, days_total, start_string=f"[+] Scraping {date}")
            start_time = time.time()
            driver.get(BASE_URL.format(date=date, location=args.location, station=station))
            while "No Data Recorded" in driver.page_source:  # Wait for page to be loaded
                time.sleep(0.1)

            data = day_scraper(driver.page_source, date)
            meridiems = []
            for row in data:
                row_meridiem = get_meridiem(f"{row['date']} {row['time']}")
                if not meridiems or (meridiems and row_meridiem != meridiems[-1]):
                    meridiems.append(row_meridiem)

            if meridiems not in [  # ONLY VALID day meridiems possible, if other, must fix it
                ['AM'],  # Only data for morning
                ['PM'],  # Only data for after noon
                ['AM', 'PM'],  # Normal day with morning and afternoon data
            ]:
                data = fix_all_wrong_date(data)

            with open(args.output, "a", newline="") as file:
                csv.DictWriter(file, COLUMNS).writerows(data)

            date_start += timedelta(days=1)
            days_count += 1
        progress_bar(1, 1, start_string=f"[+] Scraping successfully completed")

    print("[+] Successfully scraped data from '{start}' to '{stop}'.".format(
        start=args.start.strftime("%Y-%m-%d"),
        stop=args.end.strftime("%Y-%m-%d"),
    ))
    exec_min, exec_sec = divmod(int(time.time() - time_start), 60)
    print("[+] Scraped {count} days in {minutes}{seconds} sec.\n".format(
        count=days_count,
        minutes=f"{exec_min} min & " if exec_min else "",
        seconds=exec_sec,
    ))
