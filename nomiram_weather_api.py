'''Get weather from API'''
import datetime
import json
import os

import requests
from geopy.geocoders import Nominatim

geolocation = Nominatim(user_agent="nomiram-app")
BASE_URL = ""
PORT = os.environ.get("LISTEN_PORT",5001)

with open("url.json",encoding="utf8") as f:
    BASE_URL = json.load(f)

def get_weather(city:str, timestamp:str = None, current_weather:bool=False) -> str | None:
    """
    Get weather from API

    Args:
        city (str): City ex: `"Moscow"`\n
        timestamp (str, optional): Time in `YYYY-MM-DDTHH:mm`. Defaults to None.\n
        current_weather (bool, optional): Get current weather. Defaults to False.

    Returns:
        str: json
    """
    # Get latitude and longitude from City name
    location = geolocation.geocode(city)
    if not location:
        return None
    params = {
        "timezone": "auto", 
        "latitude": location.latitude, 
        "longitude": location.longitude
    }
    if current_weather:
        params["current_weather"] = current_weather
    if timestamp:
        # Request hourly temperature from API
        date = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")
        params["start_date"] = date.strftime("%Y-%m-%d")
        params["end_date"] = date.strftime("%Y-%m-%d")
        params["hourly"]="temperature_2m"
    resp = requests.get(BASE_URL,params=params,timeout=10)
    return resp.text

def get_temperature(city:str, timestamp:str = None, current_weather:bool=False) -> float | None:
    """
    Get temperature from API

    Args:
        city (str): City ex: `"Moscow"`\n
        timestamp (str, optional): Time in `YYYY-MM-DDTHH:mm`. Defaults to None.\n
        current_weather (bool, optional): Get current weather. Defaults to False.

    Returns:
        float: temperature in Celsius
    """
    resp_t = get_weather(city=city,
                       current_weather=current_weather,
                       timestamp=timestamp)
    if resp_t is None:
        return None
    json_resp = json.loads(resp_t)
    if timestamp:
        # return temperature by hour (0-23) from hourly temperature (0-24) from API
        date = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")
        return float(json_resp["hourly"]["temperature_2m"][date.hour])
    if current_weather:
        return float(json_resp["current_weather"]["temperature"])
    return None


if __name__ == "__main__":
    print(get_temperature("Moscow",current_weather=True))
    print(get_temperature("Moscow",timestamp="2023-02-17T13:00"))
