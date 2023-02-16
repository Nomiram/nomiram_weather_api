FROM python:3
COPY . /app
RUN pip3 install -r /app/requirements.txt
CMD [ "python3", "/app/nomiram_weather_api.py"]