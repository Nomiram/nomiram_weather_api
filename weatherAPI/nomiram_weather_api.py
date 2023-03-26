'''Get weather from API'''
import datetime
import json
import logging
import os

import auth_pb2_grpc
import grpc
import requests
# pylint: disable=no-name-in-module
from auth_pb2 import AuthRequest
from flask import Flask, jsonify, request
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)

geolocation = Nominatim(user_agent="nomiram-app")
PORT = os.environ.get("LISTEN_PORT", 5001)

BASE_URL = os.environ.get("API_URL")
AUTH_HEADER = 'Own-Auth-UserName'


class APIException(Exception):
    '''Exception that may used when API return not 200 status'''


def get_weather(city: str, timestamp: str = None,
                current_weather: bool = False) -> str | None:
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
        raise APIException("Location not found")
    tf = TimezoneFinder()
    timezone = tf.timezone_at(lng=location.longitude, lat=location.latitude)

    params = {
        "timezone": timezone,
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
        params["hourly"] = "temperature_2m"
    resp = requests.get(BASE_URL, params=params, timeout=10)
    if resp.status_code != 200:
        logging.error(resp.text)
        raise APIException(json.loads(resp.text))

    return resp.text


def auth(username: str) -> bool:
    """Request auth service by grpc

    Args:
        username (str): check username is in whitelist

    Returns:
        bool: true - success
    """
    connect_string = f'{os.getenv("GRPC_ADDR","localhost")}:{os.getenv("GRPC_PORT","50051")}'
    with grpc.insecure_channel(connect_string) as channel:
        stub = auth_pb2_grpc.AuthServiceStub(channel=channel)
        resp = stub.CheckAuthorization(AuthRequest(username=username))
        return resp.check


def get_temperature(city: str, timestamp: str = None,
                    current_weather: bool = False) -> float | None:
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
        # return temperature by hour (0-23) from hourly temperature (0-24) from
        # API
        date = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")
        logging.debug(json_resp)
        if json_resp.get("hourly", None) is None:
            return None
        return float(json_resp["hourly"]["temperature_2m"][date.hour])
    if current_weather:
        return float(json_resp["current_weather"]["temperature"])
    return None


@app.route("/v1/forecast/")
def v1_get_temperature_forecast():
    """
    Return temperature forecast by date and time

    Returns:
        str: json
    """
    if AUTH_HEADER in request.headers:
        auth_res = auth(request.headers[AUTH_HEADER])
        if not auth_res:
            return jsonify({"error": "Forbidden"}), 403
    else:
        return jsonify({"error": "Forbidden"}), 403
    city = request.args.get("city")
    dt = request.args.get("dt")
    if not city or not dt:
        return jsonify({"error": "city and dt must provided"}), 400
    temperature = None
    try:
        temperature = get_temperature(city=city, timestamp=dt)
    except APIException as e:
        return jsonify({"error": str(e)}), 500
    if temperature is None:
        return jsonify({"error": "Internal Server Error"}), 500
    return jsonify({"city": city, "unit": "celsius",
                   "temperature": temperature})


@app.route("/v1/current/")
def v1_get_temperature_now():
    """
    Return current temperature

    Returns:
        str: json
    """
    if AUTH_HEADER in request.headers:
        auth_res = auth(request.headers[AUTH_HEADER])
        if not auth_res:
            return jsonify({"error": "Forbidden"}), 403
    else:
        return jsonify({"error": "Forbidden"}), 403
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "city must provided"}), 400

    temperature = None
    try:
        temperature = get_temperature(city=city, current_weather=True)
    except APIException as e:
        return jsonify({"error": json.loads(str(e))}), 500
    if temperature is None:
        return jsonify({"error": "Internal Server Error"}), 500
    return jsonify({'city': city, "unit": "celsius",
                   "temperature": temperature})


if __name__ == "__main__":
    app.run("0.0.0.0", port=PORT)
