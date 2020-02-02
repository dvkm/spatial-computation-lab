import os
import json
import requests
import datetime
from dateutil import tz, relativedelta


def format_date(datetime):
    """
    Turns datetime into the url format that is required by the api
    """
    return f"{datetime.year}{str(datetime.month).zfill(2)}{str(datetime.day).zfill(2)}"

def next_date(prev_start):
    """
    Returns the first date of the next month and the last date of the next month
    """
    start_date = prev_start + relativedelta.relativedelta(months=1)
    end_date = start_date + relativedelta.relativedelta(months=1) - relativedelta.relativedelta(days=1)
    return (start_date, end_date)

def get_time(timestamp):
    """
    Turns the timestamp returned by the api into human readable time
    """
    time = datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=(timestamp))
    return time.astimezone(tz.gettz('America/New_York')).strftime("%Y/%m/%d %H:%M")


if __name__ == "__main__":
    if not os.path.exists("data"):
        os.makedirs("data")
        
    hourly = open("hourly.csv", "w")
    hourly.write("time,temperature,dew point,humidity,wind,wind speed,wind gust,pressure,precip.,snow,condition\n") # CSV heading
    num = 1

    start_date = datetime.datetime(1948, 1, 1)
    end_date = start_date + relativedelta.relativedelta(months=1) - relativedelta.relativedelta(days=1)

    # URL of the api
    BASE_URL = "https://api.weather.com/v1/location/KCLE:9:US/observations/historical.json?apiKey=6532d6454b8aa370768e63d6ba5a832e&units=e&startDate={startdate}&endDate={enddate}"

    r = requests.get(BASE_URL.format(startdate=format_date(start_date), enddate=format_date(end_date)))

    while True:
        if r.status_code != 200: # Api returns 400 if the date is out of range.
            print(f"Status code {r.status_code}. Stopping")
            break

        data = r.json()
        for observation in data["observations"]: # Observations are made approx. every hour.
            time = get_time(observation["valid_time_gmt"]) # Time of recording
            temp = observation["temp"] or 0 # Temperature
            dew = observation["dewPt"] or 0 # Dew point
            humidity = observation["rh"] or 0 # Humidity
            wind = observation["wdir_cardinal"] or "" # Wind direction
            wind_speed = observation["wspd"] or 0 # Wind speed
            gust = observation["gust"] or 0 # Gust
            pressure = observation["pressure"] or 0 # Pressure
            precip = observation["precip_hrly"] or 0 # Precipitation
            snow = observation["snow_hrly"] or 0 # Amount of snow
            condition = observation["wx_phrase"] or "" # Weather condition (windy/sunny/etc.)
            
            hourly.write(f"{time},{temp},{dew},{humidity},{wind},{wind_speed},{gust},{pressure},{precip},{snow},{condition}\n")
        
        hourly.flush() # Flush occasionally to see the progress.

        f = open(f"data/{start_date.year}-{str(start_date.month).zfill(2)}.json", "w")
        json.dump(data, f) # Write the exact response so that it can be reprocessed later if necessary

        print(f"Done with {start_date.year}/{str(start_date.month).zfill(2)}")

        # Work on the next day
        num += 1
        start_date, end_date = next_date(start_date) # Get new dates
        r = requests.get(BASE_URL.format(startdate=format_date(start_date), enddate=format_date(end_date)))