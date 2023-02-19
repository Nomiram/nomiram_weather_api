FROM python:3
COPY ./requirements.txt /app/requirements.txt
RUN pip3 install -r /app/requirements.txt
COPY . /app
CMD [ "python3", "/app/nomiram_weather_api.py"]