'''Get weather from API'''

import datetime
import json
import logging
import os

import auth_pb2_grpc
import grpc
import redis
from redis.cluster import RedisCluster
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

FEATURE_REDIS = bool(os.getenv("REDIS_SERVER"))
FEATURE_REDIS_CLUSTER = bool(os.getenv("REDIS_CLUSTER"))
BASE_URL = os.environ.get("API_URL")
AUTH_HEADER = 'Own-Auth-UserName'

# Global Cluster info
CLUSTER = None


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
    date = datetime.datetime.now()
    if timestamp:
        date = datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M")

    get_date = date.strftime("%Y-%m-%dT%H:00")
    if FEATURE_REDIS:
        req = requests.get(
            f"http://localhost:{PORT}/v1/redis/",
            params={"key": f"{city}/{get_date}"},
            timeout=200,
        )
        if req.status_code == 200:
            logging.debug("cache found in redis: %s, %s",
                          req.status_code, req.text)
            return float(req.json()["value"])
        logging.debug("not found in redis: %s, %s", req.status_code, req.text)
    resp_t = get_weather(city=city,
                         current_weather=current_weather,
                         timestamp=timestamp)
    if resp_t is None:
        return None
    json_resp = json.loads(resp_t)
    temperature = None
    if timestamp:
        # return temperature by hour (0-23) from hourly temperature (0-24) from
        # API
        logging.debug(json_resp)
        if json_resp.get("hourly", None) is None:
            return None
        temperature = float(json_resp["hourly"]["temperature_2m"][date.hour])
    if current_weather:
        temperature = float(json_resp["current_weather"]["temperature"])
    if FEATURE_REDIS:
        req_set = requests.put(
            f"http://localhost:{PORT}/v1/redis/",
            json={"key": f"{city}/{get_date}", "value": temperature},
            timeout=200,
        )
        logging.debug("redis ans: %s %s", req_set.status_code, req_set.text)
    return temperature


@app.route("/v1/forecast/")
def v1_get_temperature_forecast():
    """
    Return temperature forecast by date and time

    Returns:
        str: json
    """
    if AUTH_HEADER not in request.headers:
        return jsonify({"error": "Forbidden"}), 403
    auth_res = auth(request.headers[AUTH_HEADER])
    if not auth_res:
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
    if AUTH_HEADER not in request.headers:
        return jsonify({"error": "Forbidden"}), 403
    auth_res = auth(request.headers[AUTH_HEADER])
    if not auth_res:
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


@app.route("/v1/redis/", methods=["PUT"])
def v1_redis_set_data():
    """
    This function puts data into a Redis database using a provided key-value pair.

    Returns:
      If the "key" and "value" are provided in the JSON data and the Redis server is successfully
    connected, the function will return a JSON object with the message {"set": "OK"}. If either the
    "key" or "value" is missing from the JSON data or the Redis server cannot be connected, 
    the function will return a JSON object with an error message {"error": str} and a 500 status
    """
    json_data = request.json
    key = json_data.get("key", None)
    value = json_data.get("value", None)
    if key is None or value is None:
        return jsonify({"error": 'json {"key"=key,"value"=value} must provided'}), 500
    if not CLUSTER:
        r = redis.Redis(host=os.getenv("REDIS_SERVER"), port=os.getenv(
            "REDIS_PORT"), decode_responses=True, password=os.getenv("REDIS_PASSWORD"))
        if r.set(key, value):
            return jsonify({"set": "OK"})
        return jsonify({"error": 'can`t connect to redis'}), 500
    # else if CLUSTER
    if CLUSTER.set(key, value):
        return jsonify({"set": "OK"})
    return jsonify({"error": 'can`t connect to redis'}), 500


@app.route("/v1/redis/", methods=["GET"])
def v1_redis_get_data():
    """
    This function retrieves data from a Redis server based on a given key and returns the value if
    it exists, or a "key not found" message if it does not.

    Returns:
      If the value of the key exists in Redis, a JSON object {"value": value}. 
    If the key does not exist, a JSON object with the message {"OK": 'key not found'} 
    and a 404 status code is returned.
    """
    key = request.args.get("key", None)
    value = None
    if not CLUSTER:
        r = redis.Redis(host=os.getenv("REDIS_SERVER"), port=os.getenv(
            "REDIS_PORT"), decode_responses=True, password=os.getenv("REDIS_PASSWORD"))
        value = r.get(key)
    else:
        value = CLUSTER.get(key).decode()
    if value is not None:
        return jsonify({"value": value})
    return jsonify({"OK": 'key not found'}), 404


if __name__ == "__main__":
    if FEATURE_REDIS_CLUSTER:
        CLUSTER = RedisCluster(host=os.getenv("REDIS_SERVER"), port=os.getenv(
            "REDIS_PORT"), password=os.getenv("REDIS_PASSWORD"))
        logging.debug(CLUSTER.get_nodes())
    app.run("0.0.0.0", port=PORT)
