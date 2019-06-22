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

    # function that is called from searchWeatherForecast
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

    # function that is called from searchWeatherForecastCondition
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
            request = weather_forecast["request"]
            if request["type"] == RequestType.FIXED and request["grain"] == Grain.DAY:
                response = "Wetter {2} {1}: {0}.".format(
                weather_forecast["mainCondition"],
                weather_forecast["inLocation"],
                day_string)
                response = self.add_warning_if_needed(response, weather_forecast)
            elif request["type"] == RequestType.FIXED and request["grain"] == Grain.HOUR:
                response = "Wetter {2} um {3} {1}: {0}.".format(
                weather_forecast["mainCondition"],
                weather_forecast["inLocation"],
                day_string,
                weather_forecast["requested_time"])
        return response

    # function that is called from searchWeatherForecastTemperature
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
            request = weather_forecast["request"]
            if request["type"] == RequestType.FIXED and request["grain"] == Grain.DAY:
                if weather_forecast["time_difference"]==0:
                    response = ("{0} hat es aktuell {1} Grad. "
                                "Heute wird die Höchsttemperatur {2} Grad sein "
                                "und die Tiefsttemperatur {3} Grad.").format(
                        weather_forecast["inLocation"] if weather_forecast["inLocation"] != "" else "Hier",
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
            elif request["type"] == RequestType.FIXED and request["grain"] == Grain.HOUR:
                response = ("{2} um {3} wird es {0} {1} Grad {4}.").format(
                weather_forecast["inLocation"],
                weather_forecast["temperature"],
                day_string,
                weather_forecast["requested_time"],
                request["requested"] if request["requested"] != "" else "haben")
        return response

    # function getting and parsing output from open weather map
    def get_open_weather_map_forecast(self, request):
        location = request["location"]
        if location == "":
            location = self.default_city_name
        forecast_url = "{0}/forecast?q={1}&APPID={2}&units={3}&lang=de".format(
            self.weather_api_base_url, location, self.weather_api_key, self.units)
        try:
            response = requests.get(forecast_url)
            response = response.json()
            
            if response["cod"] == "401" or response["cod"] == "404" or response["cod"] == "429":
                return {'rc': 2} # Error: something went wrong with the api call
            
            # Parse the output of Open Weather Map's forecast endpoint
            forecasts = {}
            for x in response["list"]:
                if str(date.fromtimestamp(x["dt"])) not in forecasts:
                    forecasts[str(date.fromtimestamp(x["dt"]))] = list(filter(lambda forecast: date.fromtimestamp(forecast["dt"]) == date.fromtimestamp(x["dt"]), response["list"]))
                    
            weather = {}
            for key,forecast in forecasts.items():
                weather[key] = {
                                "rc": 0,
                                "type": "weather",
                                "date": datetime.strptime(key, "%Y-%m-%d").date(),
                                "location": location,
                                "time": [datetime.strptime(x, "%H:%M:%S").time() for x in [x["dt_txt"].split(" ")[1] for x in forecast]],
                                "temperature": [x["main"]["temp"] for x in forecast],
                                "weather condition": [x["weather"][0]["main"] for x in forecast],
                                "weather description": [x["weather"][0]["description"] for x in forecast],
                                "pressure": [x["main"]["pressure"] for x in forecast],
                                "humidity": [x["main"]["humidity"] for x in forecast],
                                "wind speed": [x["wind"]["speed"] for x in forecast],
                                "wind direction": [x["wind"]["deg"] for x in forecast]
                               }
            return weather
        except (requests.exceptions.ConnectionError, ValueError):
            return {'rc': 1}  # Error: No internet connection

    def get_weather_forecast(self, intent_message):
        request = self.parse_intent_request(intent_message)
        weatherforecast = self.get_open_weather_map_forecast(request)
        if weatherforecast.get("rc", 0) != 0:
            return weatherforecast
        else:
            try:
                if request["type"] == RequestType.FIXED:
                    if request["grain"] == Grain.DAY:
                        return self.get_weather_fixed_day(request, weatherforecast[request["startdate"]])
                    elif request["grain"] == Grain.HOUR:
                        return self.get_weather_fixed_hour(request, weatherforecast[request["startdate"]])
                elif request["type"] == RequestType.INTERVAL: 
                    if request["grain"] == Grain.DAY:
                        return {'rc': 4}
                    elif request["grain"] == Grain.HOUR:
                        return {'rc': 4}
                else:
                    return {'rc': -1}
            except KeyError:
                return {'rc': 3} # to many days in advance

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
            index = -1
            for x in range(len(weather["time"])-1):
                if weather["time"][x] <= datetime.now().time() < weather["time"][x+1]:
                    index=x
            return {
                    "rc": 0,
                    "request": request,
                    "inLocation": " in {0}".format(request["location"]) if request["location"] else "",
                    "temperature": int(weather["temperature"][index]),
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
        request = { "type": RequestType.FIXED, "grain": Grain.DAY, "startdate": datetime.now().strftime("%Y-%m-%d"), "enddate": "", "starttime": "", "endtime": "", "location": "", "requested": ""}
        locations = []
        
        if intent_message.slots.forecast_start_date_time.first() is not None:
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
        elif intent_message.slots.forecast_locality.first() is not None:
            request["location"] = intent_message.slots.forecast_locality.first().value
        elif intent_message.slots.forecast_condition_name.first() is not None:
            request["requested"] = intent_message.slots.forecast_condition_name.first().value
        elif intent_message.slots.forecast_temperature_name.first() is not None:
            request["requested"] = intent_message.slots.forecast_temperature_name.first().value
        elif intent_message.slots.forecast_item.first() is not None:
            request["requested"] = intent_message.slots.forecast_item.first().value
        return request

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
        
    @staticmethod
    def add_warning_if_needed(response, weather_forecast):
        if weather_forecast["rain"] and "rain" not in weather_forecast["mainCondition"]\
                and "regen" not in weather_forecast["mainCondition"]:
            response += ' Es könnte regnen.'
        if weather_forecast["snow"] and "snow" not in weather_forecast["mainCondition"]:
            response += ' Es könnte schneien.'
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
            if temp_day < 7:
                day_string="am " + weather_forecast["weekday"]
            elif temp_day < 14:
                day_string="nächste Woche " + weather_forecast["weekday"]
            else:
                day_string="am " + weather_forecast["requested_date"]
            
        return day_string
