# -*- encoding: utf-8 -*-
import requests
from datetime  import date, time, datetime, timedelta
import random
import locale
import hermes_python.ontology.dialogue.slot as hermes_slots
from enum import Enum
from hermes_python.ffi.ontology import Grain
from weather_helper import WeatherRequest, DateType, ForecastType
import copy

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
        print("forecast")
        """
                Complete answer:
                    - condition
                    - max and min temperature
                    - warning about rain or snow if needed
        """
        requests = self.parse_intent_request(intent_message)
        response = ""
        print("Requests: " + str(len(requests)))
        print(*requests, sep='\n')
        for request in requests:
            weather_forecast = self.get_weather_forecast(request)
            if weather_forecast.get("rc", 0) != 0:
                response = response + self.error_response(weather_forecast)
            else:
                if request.date_type == DateType.FIXED and request.grain == Grain.DAY:
                    response = response + ("Wetter {4} {1}: {0}. "
                                "Die Temperatur ist zwischen {3} und {2} Grad. ").format(
                        weather_forecast["mainCondition"],
                        request.output_location,
                        weather_forecast["temperatureMax"],
                        weather_forecast["temperatureMin"],
                        request.output_day)
                    response = response + self.add_warning_if_needed(weather_forecast)
                elif request.date_type == DateType.FIXED and request.grain == Grain.HOUR:
                    response = response + ("Das Wetter {3} um {4} {1}: {0}. "
                                "Die Temperatur ist {2} Grad. ").format(
                        weather_forecast["mainCondition"],
                        request.output_location,
                        weather_forecast["temperature"],
                        request.output_day,
                        request.readable_start_time)
        return response

    # function that is called from searchWeatherForecastCondition
    def forecast_condition(self, intent_message):
        print("forecast_condition")
        """
        Condition-focused answer:
            - condition
            - warning about rain or snow if needed
        """
        requests = self.parse_intent_request(intent_message)
        response = ""
        print("Requests: " + str(len(requests)))
        print(*requests, sep='\n')
        for request in requests:
            weather_forecast = self.get_weather_forecast(request)
            if weather_forecast.get("rc", 0) != 0:
                response = response + self.error_response(weather_forecast)
            else:
                if request.date_type == DateType.FIXED and request.grain == Grain.DAY:
                    response = response + "Wetter {2} {1}: {0}.".format(
                    weather_forecast["mainCondition"],
                    request.output_location,
                    request.output_day)
                    response = response + self.add_warning_if_needed(weather_forecast)
                elif request.date_type == DateType.FIXED and request.grain == Grain.HOUR:
                    response = response + "Wetter {2} um {3} {1}: {0}.".format(
                    weather_forecast["mainCondition"],
                    request.output_location,
                    request.output_day,
                    request.readable_start_time)
        return response

    # function that is called from searchWeatherForecastTemperature
    def forecast_temperature(self, intent_message):
        print("forecast_temperature")
        """
        Temperature-focused answer:
            - current temperature (for today only)
            - max and min temperature
        """
        requests = self.parse_intent_request(intent_message)
        response = ""
        print("Requests: " + str(len(requests)))
        print(*requests, sep='\n')
        for request in requests:
            weather_forecast = self.get_weather_forecast(request)
            if weather_forecast['rc'] != 0:
                response = response + self.error_response(weather_forecast)
            else:
                if request.date_type == DateType.FIXED and request.grain == Grain.DAY:
                    if request.time_difference == 0:
                        response = response + ("{0} hat es aktuell {1} Grad. "
                                    "Heute wird die Höchsttemperatur {2} Grad sein "
                                    "und die Tiefsttemperatur {3} Grad.").format(
                            request.output_location if request.output_location != "" else "Hier",
                            weather_forecast["temperature"],
                            weather_forecast["temperatureMax"],
                            weather_forecast["temperatureMin"])
                    else:
                        response = response + ("{4} wird die Höchsttemperatur {2} Grad sein "
                                "und die Tiefsttemperatur {3} Grad.").format(
                        request.output_location,
                        weather_forecast["temperature"],
                        weather_forecast["temperatureMax"],
                        weather_forecast["temperatureMin"],
                        request.output_day)
                elif request.date_type == DateType.FIXED and request.grain == Grain.HOUR:
                    response = response + ("{2} um {3} wird es {0} {1} Grad {4}.").format(
                    request.output_location,
                    weather_forecast["temperature"],
                    request.output_day,
                    request.readable_start_time,
                    request.requested if request.requested != "" else "haben")
        return response

    # function getting and parsing output from open weather map
    def get_open_weather_map_forecast(self, request):
        print("get_open_weather_map_forecast")
        location = request.location
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

    def get_weather_forecast(self, request):
        print("get_weather_forecast")
        weatherforecast = self.get_open_weather_map_forecast(request)
        if weatherforecast.get("rc", 0) != 0:
            return weatherforecast
        else:
            try:
                if request.date_type == DateType.FIXED:
                    if request.grain == Grain.DAY:
                        return self.get_weather_fixed_day(request, weatherforecast[request.string_date])
                    elif request.grain == Grain.HOUR:
                        return self.get_weather_fixed_hour(request, weatherforecast[request.string_date])
                    elif request.grain == Grain.WEEK:
                        return {'rc': 4}
                    elif request.grain == Grain.MONTH:
                        return {'rc': 4}
                elif request.date_type == DateType.INTERVAL: 
                    if request.grain == Grain.DAY:
                        return {'rc': 4}
                    elif request.grain == Grain.HOUR:
                        return {'rc': 4}
                else:
                    return {'rc': -1}
            except KeyError:
                return {'rc': 3} # to many days in advance

    def get_weather_fixed_hour(self, request, weather):
        print("get_weather_fixed_hour")
        if weather['rc'] != 0:
            return weather
        else:
            index = -1
            for x in range(len(weather["time"])-1):
                if weather["time"][x] <= request.start_time < weather["time"][x+1]:
                    index=x
            return {
                    "rc": 0,
                    "temperature": int(weather["temperature"][index]),
                    "rain": weather["weather condition"][index] == "Rain",
                    "snow": weather["weather condition"][index] == "Snow",
                    "mainCondition": weather["weather description"][index]
                   }

    def get_weather_fixed_day(self, request, weather):
        print("get_weather_fixed_day")
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
                    "temperature": int(weather["temperature"][index]),
                    "temperatureMin": int(min(weather["temperature"])),
                    "temperatureMax": int(max(weather["temperature"])),
                    "rain": "Rain" in weather["weather condition"],
                    "snow": "Snow" in weather["weather condition"],
                    "mainCondition": max(set(weather["weather description"]), key=weather["weather description"].count).lower()
                   }

    def parse_intent_request(self, intent_message):
        # Parse the query slots
        
        requests = []
        #intent
        intent = None
        
        if "searchWeatherForecastCondition" in intent_message.intent.intent_name:
            intent = ForecastType.CONDITION
        elif "searchWeatherForecastItem" in intent_message.intent.intent_name:
            intent = ForecastType.ITEM
        elif "searchWeatherForecastTemperature" in intent_message.intent.intent_name:
            intent = ForecastType.TEMPERATURE
        elif  "searchWeatherForecast" in intent_message.intent.intent_name:
            intent = ForecastType.FULL
        # date and time
        date_times = intent_message.slots.forecast_start_date_time.all()
        if date_times is not None:
            for start_date_time in date_times:
                new_request = None
                if type(start_date_time) is hermes_slots.InstantTimeValue:
                    new_request = WeatherRequest(DateType.FIXED, start_date_time.grain, start_date_time.value.split(' ')[0], intent)
                    if new_request.grain == Grain.SECOND:
                        new_request.grain = Grain.HOUR
                        new_request.start_time = start_date_time.value.split(' ')[1].split(".")[0]
                        print(start_date_time.value)
                    elif new_request.grain == Grain.HOUR:
                        new_request.start_time = start_date_time.value.split(' ')[1]
                elif type(start_date_time) is hermes_slots.TimeIntervalValue:
                    new_request = WeatherRequest(RequestType.INTERVAL, Grain.DAY, start_date_time.from_date.split(' ')[0])
                    new_request.start_time = start_date_time.from_date.split(' ')[1]
                    new_request.start_time = start_date_time.to_date.split(' ')[1]
                    if start_date_time.from_date.split(' ')[0] == start_date_time.to_date.split(' ')[0]:
                        new_request.grain = Grain.HOUR
                if new_request is not None:
                    requests.append(new_request)
        else:
            requests.append(WeatherRequest(DateType.FIXED, Grain.DAY, date.today(), intent))

        # location
        locations = intent_message.slots.forecast_locality.all()
        if locations is not None and len(locations) > 0:
            tmp_requests = copy.copy(requests)
            for request in tmp_requests:
                requests.remove(request)
                for locality in locations:
                    new_request = copy.deepcopy(request)
                    new_request.location = locality.value
                    requests.append(new_request)

        # requested
        requested = None
        if intent == ForecastType.CONDITION:
            requested = intent_message.slots.forecast_condition_name.all()
        elif intent == ForecastType.ITEM:
            requested = intent_message.slots.forecast_item.all()
        elif intent == ForecastType.TEMPERATURE:
            requested = intent_message.slots.forecast_temperature_name.all()
        if requested is not None and len(requested) > 0:
            tmp_requests = copy.copy(requests)
            for request in tmp_requests:
                requests.remove(request)
                for r in requested:
                    new_request = copy.deepcopy(request)
                    new_request.requested = r.value
                    requests.append(new_request)
                    
        return requests

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
    def add_warning_if_needed(weather_forecast):
        response = ""
        if weather_forecast["rain"] and "rain" not in weather_forecast["mainCondition"]\
                and "regen" not in weather_forecast["mainCondition"]:
            response = ' Es könnte regnen.'
        if weather_forecast["snow"] and "snow" not in weather_forecast["mainCondition"]:
            response = ' Es könnte schneien.'
        return response

