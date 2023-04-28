import csv
from datetime import datetime, timedelta
from argparse import ArgumentParser

from util import dt_from_str, dt_to_str, progress_bar, COLUMNS


def get_data_for_datetime(data: list, date: datetime):
    return [row for row in data if all([
        # We want to sort by date and hours
        row["datetime"].month == date.month,
        row["datetime"].day == date.day,
        row["datetime"].hour == date.hour
    ])]


def parse_command_line(custom_args=None):
    parser = ArgumentParser()
    parser.add_argument("filename")
    return parser.parse_args(custom_args)


AVERAGE_COLUMNS = ["temperature", "dew_point", "humidity", "wind_speed", "wind_gust", "pressure", "precipitation"]

args = parse_command_line()
print(f"[+] Parsing '{args.filename}'... ", end="", flush=True)
with open(args.filename, "r") as file:
    reader = csv.DictReader(file, COLUMNS)
    next(reader)  # Remove header
    data = [{
        "datetime": dt_from_str(f"{row['date']} {row['time']}"),
        "temperature": float(row["temperature"]),
        "dew_point": float(row["dew_point"]),
        "humidity": float(row["humidity"]),
        "wind": row["wind"],
        "wind_speed": float(row["wind_speed"]),
        "wind_gust": float(row["wind_gust"]),
        "pressure": float(row["pressure"]),
        "precipitation": float(row["precipitation"]),
        "condition": row["condition"]
    } for row in reader]
print("Done!")

date = datetime(2020, 1, 1, 0, 0, 0)
date_end = datetime(2020, 12, 31, 23, 59, 59)
number_of_periodes = ((date_end - date).days + 1) * 24
number_of_periodes_done = 0

average_data = []
progress_bar(number_of_periodes_done, number_of_periodes, start_string="[+] Averaging data")
while date <= date_end:
    matching_data = get_data_for_datetime(data, date)
    if len(matching_data):
        averages = dict([(item, 0) for item in AVERAGE_COLUMNS])
        for match in matching_data:
            for column in AVERAGE_COLUMNS:
                averages[column] += match[column]

        # now we make the sum for every column, divide by number of matching data to make the average
        for column in AVERAGE_COLUMNS:
            averages[column] = round(averages[column] / len(matching_data), ndigits=3)

        # Now add the date and hour and add it into list
        averages["date"], averages["time"] = dt_to_str(date, fmt="%m-%d %H:%M").split(" ")

        average_data.append(averages)

    # end of loop
    date += timedelta(hours=1)
    number_of_periodes_done += 1
    progress_bar(number_of_periodes_done, number_of_periodes, start_string="[+] Averaging data")

header = ["date", "time"]  # need it to be first
header.extend(AVERAGE_COLUMNS)

output = args.filename.split(".")[0] + "_avg_hour.csv"
with open(output, "w", newline="") as file:
    writer = csv.DictWriter(file, header)
    writer.writeheader()
    writer.writerows(average_data)
print(f"[+] Average data have been written to '{output}'.")
