# -*- encoding: utf-8 -*-
import requests
from datetime  import date, time, datetime, timedelta
import random
import locale
import hermes_python.ontology.dialogue.slot as hermes_slots
from enum import Enum
from hermes_python.ffi.ontology import Grain

class RequestType(Enum):
    FIXED = "fixed"
    INTERVAL = "interval"

class Weather:
    def __init__(self, config):
        self.fromtimestamp = datetime.fromtimestamp
        self.weather_api_base_url = "http://api.openweathermap.org/data/2.5"
        try:
            self.weather_api_key = config['secret']['openweathermap_api_key']
        except KeyError:
            self.weather_api_key = "XXXXXXXXXXXXXXXXXXXXX"
        try:
            self.default_city_name = config['secret']['default_city']
        except KeyError:
            self.default_city_name = "Berlin"
        try:
            self.units = config['global']['units']
        except KeyError:
            self.units = "metric"
        try:
            locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
        except locale.Error:
            print("That locale doesn't exist on the system")

    def get_open_weather_map_forecast(self, location):
        print("get_open_weather_map_forecast: start")
        if location == "":
            location = self.default_city_name
        forecast_url = "{0}/forecast?q={1}&APPID={2}&units={3}&lang=de".format(
            self.weather_api_base_url, location, self.weather_api_key, self.units)
        try:
            r_forecast = requests.get(forecast_url)
            
            if r_forecast.json()["cod"] == "401" or r_forecast.json()["cod"] == "404" or r_forecast.json()["cod"] == "429":
                print("get_open_weather_map_forecast: error rc:2")
                return {'rc': 2} # Error: something went wrong with the api call
            print("get_open_weather_map_forecast: return")
            return r_forecast
        except (requests.exceptions.ConnectionError, ValueError):
            print("get_open_weather_map_forecast: error rc:1")
            return {'rc': 1}  # Error: No internet connection

    def parse_open_weather_map_forecast(self, response, date_requested_str, location):
        # Parse the output of Open Weather Map's forecast endpoint
        date_requested = datetime.strptime(date_requested_str, "%Y-%m-%d").date()

        forecasts = list(filter(lambda forecast: str(date.fromtimestamp(forecast["dt"])) == date_requested_str, response.json()["list"]))
        if forecasts != []:
            weather_for_date = {
                                "rc": 0,
                                "type": "weather",
                                "date": date_requested,
                                "location": location,
                                "time": [datetime.strptime(x, "%H:%M:%S").time() for x in [x["dt_txt"].split(" ")[1] for x in forecasts]],
                                "temperature": [x["main"]["temp"] for x in forecasts],
                                "weather condition": [x["weather"][0]["main"] for x in forecasts],
                                "weather description": [x["weather"][0]["description"] for x in forecasts],
                                "pressure": [x["main"]["pressure"] for x in forecasts],
                                "humidity": [x["main"]["humidity"] for x in forecasts],
                                "wind speed": [x["wind"]["speed"] for x in forecasts],
                                "wind direction": [x["wind"]["deg"] for x in forecasts]
                               }
            return weather_for_date
        else:
            return {'rc': 3 } # to many days in advance

    def error_response(self, data):
        error_num = data['rc']
        if error_num == 1:
            response = random.choice(["Es ist leider kein Internet verfügbar.",
                                      "Ich bin nicht mit dem Internet verbunden.",
                                      "Es ist kein Internet vorhanden."])
            if 'location' in data.keys() and data['location'] == self.default_city_name:
                response = "Schau doch aus dem Fenster. " + response
        elif error_num == 2:
            response = random.choice(["Wetter konnte nicht abgerufen werden. Entweder gibt es den Ort nicht, oder der "
                                      "API-Schlüssel ist ungültig.",
                                      "Fehler beim Abrufen. Entweder gibt es den Ort nicht, oder der API-Schlüssel "
                                      "ist ungültig."])
        elif error_num == 3:
            response = random.choice(["So weit in die Zukunft kenne ich das Wetter nicht.",
                                      "Ich kann nicht soweit in die Zukunft sehen.",
                                      "Das Wetter für diesen Tag wurde noch nicht beschlossen."])
        elif error_num == 4:
            response = random.choice(["Diese Funktion wird noch nicht unterstützt.", 
                                      "Ich habe noch nicht gelernt, wie ich diese Anfrage verarbeiten soll."])
        else:
            response = random.choice(["Es ist ein Fehler aufgetreten.", "Hier ist ein Fehler aufgetreten."])
        return response

    def get_weather_forecast(self, intent_message):
        request = self.parse_intent_request(intent_message)
        weatherforecast = self.get_open_weather_map_forecast(request["location"])
        if type(weatherforecast) is dict and weatherforecast.get("rc", 0) != 0:
            return weatherforecast
        
        if request["type"] == RequestType.FIXED:
            weather_for_date = self.parse_open_weather_map_forecast(weatherforecast, request["startdate"], request["location"])
            if request["grain"] == Grain.DAY:
                return self.get_weather_fixed_day(request, weather_for_date)
            elif request["grain"] == Grain.HOUR:
                return self.get_weather_fixed_hour(request, weather_for_date)
        elif request["type"] == RequestType.INTERVAL: 
            if request["grain"] == Grain.DAY:
                return {'rc': 4}
            elif request["grain"] == Grain.HOUR:
                return {'rc': 4}
        else:
            return {'rc': -1}

    def get_weather_fixed_hour(self, request, weather):
        if weather['rc'] != 0:
            return weather
        else:
            time_requested = datetime.strptime(request["starttime"], "%H:%M:%S").time()
            today = date.today()
            time_difference=(weather["date"]-today).days
            index = -1
            for x in range(len(weather["time"])-1):
                if weather["time"][x] <= time_requested < weather["time"][x+1]:
                    index=x
            return {
                    "rc": 0,
                    "request": request,
                    "inLocation": " in {0}".format(request["location"]) if request["location"] else "",
                    "temperature": int(weather["temperature"][index]),
                    "rain": weather["weather condition"][index] == "Rain",
                    "snow": weather["weather condition"][index] == "Snow",
                    "mainCondition": weather["weather description"][index],
                    "time_difference":time_difference,
                    "weekday":weather["date"].strftime("%A"),
                    "requested_date":weather["date"].strftime("%d. %B."),
                    "requested_time":time_requested.strftime("%H:%M")
                   }

    def get_weather_fixed_day(self, request, weather):
        if weather['rc'] != 0:
            return weather
        else:
            today = date.today()
            time_difference=(weather["date"]-today).days
            return {
                    "rc": 0,
                    "request": request,
                    "inLocation": " in {0}".format(request["location"]) if request["location"] else "",
                    "temperatureMin": int(min(weather["temperature"])),
                    "temperatureMax": int(max(weather["temperature"])),
                    "rain": "Rain" in weather["weather condition"],
                    "snow": "Snow" in weather["weather condition"],
                    "mainCondition": max(set(weather["weather description"]), key=weather["weather description"].count).lower(),
                    "time_difference":time_difference,
                    "weekday":weather["date"].strftime("%A"),
                    "requested_date":weather["date"].strftime("%d. %B")
                }

    def parse_intent_request(self, intent_message):
        # Parse the query slots
        request = { "type": RequestType.FIXED, "grain": Grain.DAY, "startdate": datetime.now().strftime("%Y-%m-%d"), "enddate": "", "starttime": "", "endtime": "", "location": ""}
        locations = []

        for (slot_value, slot) in intent_message.slots.items():
            if slot_value not in ['forecast_condition_name', 'forecast_start_date_time',
                                  'forecast_item', 'forecast_temperature_name']:
                locations.append(slot[0].slot_value.value)
            elif slot_value == 'forecast_start_date_time':
                start_date_time = intent_message.slots.forecast_start_date_time.first()
                if type(start_date_time) is hermes_slots.InstantTimeValue:
                    request["type"] = RequestType.FIXED
                    request["startdate"] = start_date_time.value.split(' ')[0]
                    request["grain"] = start_date_time.grain
                    if request["grain"] == Grain.HOUR:
                        request["starttime"] = start_date_time.value.split(' ')[1]
                elif type(intent_message.slots.forecast_start_date_time.first()) is hermes_slots.TimeIntervalValue:
                    request["type"] = RequestType.INTERVAL
                    request["startdate"] = intent_message.slots.forecast_start_date_time.first().from_date.split(' ')[0]
                    request["starttime"] = intent_message.slots.forecast_start_date_time.first().from_date.split(' ')[1]
                    request["enddate"] = intent_message.slots.forecast_start_date_time.first().to_date.split(' ')[0]
                    request["endtime"] = intent_message.slots.forecast_start_date_time.first().to_date.split(' ')[1]
                    if request["startdate"] == request["enddate"]:
                        request["grain"] == Grain.HOUR
                    else:
                        request["grain"] == Grain.DAY
        location_objects = [loc_obj for loc_obj in locations if loc_obj is not None]
        if location_objects:
            request["location"] = location_objects[0].value
        return request

    @staticmethod
    def add_warning_if_needed(response, weather_forecast):
        if weather_forecast["rain"] and "rain" not in weather_forecast["mainCondition"]\
                and "regen" not in weather_forecast["mainCondition"]:
            response += ' Es könnte regnen.'
        if weather_forecast["snow"] and "snow" not in weather_forecast["mainCondition"]:
            response += ' Es könnte schneien.'
        return response

    def forecast(self, intent_message):
        """
                Complete answer:
                    - condition
                    - max and min temperature
                    - warning about rain or snow if needed
        """
        weather_forecast = self.get_weather_forecast(intent_message)
        if weather_forecast.get("rc", 0) != 0:
            response = self.error_response(weather_forecast)
        else:
            day_string=self.day(weather_forecast)
            request = weather_forecast["request"]
            if request["type"] == RequestType.FIXED and request["grain"] == Grain.DAY:
                response = ("Wetter {4} {1}: {0}. "
                            "Die Temperatur ist zwischen {3} und {2} Grad.").format(
                    weather_forecast["mainCondition"],
                    weather_forecast["inLocation"],
                    weather_forecast["temperatureMax"],
                    weather_forecast["temperatureMin"],
                    day_string)
                response = self.add_warning_if_needed(response, weather_forecast)
            elif request["type"] == RequestType.FIXED and request["grain"] == Grain.HOUR:
                response = ("Das Wetter {3} um {4} {1}: {0}. "
                            "Die Temperatur ist {2} Grad.").format(
                    weather_forecast["mainCondition"],
                    weather_forecast["inLocation"],
                    weather_forecast["temperature"],
                    day_string,
                    weather_forecast["requested_time"])
        return response

    def forecast_condition(self, intentMessage):
        """
        Condition-focused answer:
            - condition
            - warning about rain or snow if needed
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast.get("rc", 0) != 0:
            response = self.error_response(weather_forecast)
        else:
            day_string=self.day(weather_forecast)
            response = "Wetter {2} {1}: {0}.".format(
                weather_forecast["mainCondition"],
                weather_forecast["inLocation"],
                day_string)
            response = self.add_warning_if_needed(response, weather_forecast)
        return response

    def forecast_temperature(self, intentMessage):
        """
        Temperature-focused answer:
            - current temperature (for today only)
            - max and min temperature
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast['rc'] != 0:
            response = self.error_response(weather_forecast)
        else:
            day_string=self.day(weather_forecast)
            if weather_forecast["time_difference"]==0:
                response = ("{0} hat es aktuell {1} Grad. "
                            "Heute wird die Höchsttemperatur {2} Grad sein "
                            "und die Tiefsttemperatur {3} Grad.").format(
                    weather_forecast["inLocation"],
                    weather_forecast["temperature"],
                    weather_forecast["temperatureMax"],
                    weather_forecast["temperatureMin"])
            else:
                response = ("{4} wird die Höchsttemperatur {2} Grad sein "
                        "und die Tiefsttemperatur {3} Grad.").format(
                weather_forecast["inLocation"],
                weather_forecast["temperature"],
                weather_forecast["temperatureMax"],
                weather_forecast["temperatureMin"],
                day_string)
        return response

    @staticmethod
    def day(weather_forecast):
        """
        Takes the time difference to today to figure out which day it will use in the response
        """
        if weather_forecast["time_difference"]==0:
            day_string="heute"
        elif weather_forecast["time_difference"]==1:
            day_string="morgen"
        else:
            temp_day=datetime.today().weekday()+weather_forecast["time_difference"]
            print(temp_day,"=",datetime.today().weekday(),"+",weather_forecast["time_difference"])
            if temp_day < 7:
                day_string="am " + weather_forecast["weekday"]
            elif temp_day < 14:
                day_string="nächste Woche " + weather_forecast["weekday"]
            else:
                day_string="am " + weather_forecast["requested_date"]
            
        return day_string
