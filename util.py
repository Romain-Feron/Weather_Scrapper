# -*- coding: utf-8 -*-
from datetime import datetime, timedelta


COLUMNS = [
    "date",
    "time",
    "temperature",
    "dew_point",
    "humidity",
    "wind",
    "wind_speed",
    "wind_gust",
    "pressure",
    "precipitation",
    "condition"
]


def farenheit_to_celcius(farenheit):
    return round((float(farenheit) - 32) * 5 / 9, 2)


def mph_to_kph(miles):
    return round(float(miles) * 1.609344, 2)


def inch_to_mm(inch):
    return round(float(inch) * 25.4, 2)


def valid_date_format(date_string: str, date_type: str):
    if not len(date_string.split("-")) == 3:
        exit(f"[!] {date_type.capitalize()} date must be in YYYY-MM-DD format.")
    return True


def dt_from_str(dt: str, fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.strptime(dt, fmt)


def dt_to_str(dt: str, fmt="%Y-%m-%d %H:%M:%S"):
    return datetime.strftime(dt, fmt)


def progress_bar(progress, total, start_string="", end=False):
    percentage = 100 * (progress / float(total))
    bar = '█' * int(percentage) + '-' * (100 - int(percentage))
    print(f"\r{start_string} |{bar}| {percentage:.2f}%", end="\r")
    if percentage == 100.0:
        print()  # Ensure we do not overwrite progress bar


def get_meridiem(dt: str):
    return dt_to_str(dt=dt_from_str(dt), fmt="%p")


def _fix_wrong_date(rows: list, meridiem_to_fix: str):
    if meridiem_to_fix == "PM":
        index, step = 0, 1
    else:
        index = step = -1
    while True:
        row_date = f"{rows[index]['date']} {rows[index]['time']}"
        if get_meridiem(row_date) != meridiem_to_fix:  # Then stop
            break
        row_date_corrected = dt_to_str(dt_from_str(row_date) + timedelta(days=-step))
        rows[index]["date"], rows[index]["time"] = row_date_corrected.split(" ")
        index += step
    return rows


def fix_all_wrong_date(rows: list):
    rows = _fix_wrong_date(rows, "AM")
    rows = _fix_wrong_date(rows, "PM")
    return rows
