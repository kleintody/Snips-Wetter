# -*- encoding: utf-8 -*-
import requests
from datetime  import date, time, datetime, timedelta
import random
import locale
import hermes_python.ontology.dialogue.slot as hermes_slots
from hermes_python.ffi.ontology import Grain, Precision

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
            
    def parse_open_weather_map_forecast_response(self, response, location, date_requested_str, time_requested_str):
        # Parse the output of Open Weather Map's forecast endpoint
        try:
            date_requested = datetime.strptime(date_requested_str, "%Y-%m-%d").date()
            today = date.today()
            time_difference=(date_requested-today).days
            forecasts = list(filter(lambda forecast: str(date.fromtimestamp(forecast["dt"])) == date_requested_str, response["list"]))
            all_time_str = [x["dt_txt"].split(" ")[1] for x in forecasts]
            all_time = [datetime.strptime(x, "%H:%M:%S").time() for x in all_time_str]
            all_min = [x["main"]["temp_min"] for x in forecasts]
            all_max = [x["main"]["temp_max"] for x in forecasts]
            all_conditions = [x["weather"][0]["description"] for x in forecasts]
            all_weather = [x["weather"][0]["main"] for x in forecasts]
            rain = list(filter(lambda forecast: forecast["weather"][0]["main"] == "Rain", forecasts))
            snow = list(filter(lambda forecast: forecast["weather"][0]["main"] == "Snow", forecasts))
            
            if time_requested_str != "":
                time_requested = datetime.strptime(time_requested_str, "%H:%M:%S").time()
                index = -1
                for x in range(len(all_time)-1):
                    if all_time[x] <= time_requested < all_time[x+1]:
                        index=x
                return {
                    "rc": 0,
                    "grain": "hour",
                    "location": location,
                    "inLocation": " in {0}".format(location) if location else "",
                    "temperature": int(forecasts[index]["main"]["temp"]),
                    "temperatureMin": all_min[index],
                    "temperatureMax": all_max[index],
                    "rain": all_weather[index] == "Rain",
                    "snow": all_weather[index] == "Snow",
                    "mainCondition": all_conditions[index],
                    "time_difference":time_difference,
                    "weekday":date_requested.strftime("%A"),
                    "requested_date":date_requested.strftime("%d. %B"),
                    "requested_time":time_requested.strftime("%H:%M")
                }
            else:
                return {
                    "rc": 0,
                    "grain": "day",
                    "location": location,
                    "inLocation": " in {0}".format(location) if location else "",
                    "temperature": int(forecasts[0]["main"]["temp"]),
                    "temperatureMin": int(min(all_min)),
                    "temperatureMax": int(max(all_max)),
                    "rain": len(rain) > 0,
                    "snow": len(snow) > 0,
                    "mainCondition": max(set(all_conditions), key=all_conditions.count).lower(),
                    "time_difference":time_difference,
                    "weekday":date_requested.strftime("%A"),
                    "requested_date":date_requested.strftime("%d. %B")
                }
        except KeyError:  # error 404 (locality not found or api key is wrong)
            return {'rc': 2}
        except IndexError:  # forecast doesn't have that many days in advance)
            return {'rc': 3}
    
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
        else:
            response = random.choice(["Es ist ein Fehler aufgetreten.", "Hier ist ein Fehler aufgetreten."])
        return response

    def get_weather_forecast(self, intentMessage):
        # Parse the query slots, and fetch the weather forecast from Open Weather Map's API
        locations = []
        date_requested = datetime.now().strftime("%Y-%m-%d")
        time_requested = ""
        for (slot_value, slot) in intentMessage.slots.items():
            if slot_value not in ['forecast_condition_name', 'forecast_start_date_time',
                                  'forecast_item', 'forecast_temperature_name']:
                locations.append(slot[0].slot_value.value)
            elif slot_value == 'forecast_start_date_time':
                start_date_time = intentMessage.slots.forecast_start_date_time.first()
                if type(start_date_time) is hermes_slots.InstantTimeValue:
                    if start_date_time.grain == Grain.DAY:
                        date_requested=start_date_time.value.split(' ')[0]
                    elif start_date_time.grain == Grain.HOUR:
                        date_requested=start_date_time.value.split(' ')[0]
                        time_requested=start_date_time.value.split(' ')[1]
                elif type(intentMessage.slots.forecast_start_date_time.first()) is hermes_slots.TimeIntervalValue:
                    print("Not supported")
                    print(intentMessage.slots.forecast_start_date_time.first().from_date)
                    print(intentMessage.slots.forecast_start_date_time.first().to_date)
        location_objects = [loc_obj for loc_obj in locations if loc_obj is not None]
        if location_objects:
            location = location_objects[0].value
        else:
            location = self.default_city_name
        forecast_url = "{0}/forecast?q={1}&APPID={2}&units={3}&lang=de".format(
            self.weather_api_base_url, location, self.weather_api_key, self.units)
        try:
            r_forecast = requests.get(forecast_url)
            return self.parse_open_weather_map_forecast_response(r_forecast.json(), location, date_requested, time_requested)
        except (requests.exceptions.ConnectionError, ValueError):
            return {'rc': 1}  # Error: No internet connection

    @staticmethod
    def add_warning_if_needed(response, weather_forecast):
        if weather_forecast["rain"] and "rain" not in weather_forecast["mainCondition"]\
                and "regen" not in weather_forecast["mainCondition"]:
            response += ' Es könnte regnen.'
        if weather_forecast["snow"] and "snow" not in weather_forecast["mainCondition"]:
            response += ' Es könnte schneien.'
        return response

    def forecast(self, intentMessage):
        """
                Complete answer:
                    - condition
                    - max and min temperature
                    - warning about rain or snow if needed
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast['rc'] != 0:
            response = self.error_response(weather_forecast)
        else:
            day_string=self.day(weather_forecast)
            if weather_forecast["grain"] == "day":
                response = ("Wetter {5} {1}: {0}. "
                            "Die Temperatur ist zwischen {4} und {3} Grad.").format(
                    weather_forecast["mainCondition"],
                    weather_forecast["inLocation"],
                    weather_forecast["temperature"],
                    weather_forecast["temperatureMax"],
                    weather_forecast["temperatureMin"],
                    day_string)
                response = self.add_warning_if_needed(response, weather_forecast)
            elif weather_forecast["grain"] == "hour":
                response = ("Das Wetter {5} um {6} {1}: {0}. "
                            "Die Temperatur ist {2} Grad.").format(
                    weather_forecast["mainCondition"],
                    weather_forecast["inLocation"],
                    weather_forecast["temperature"],
                    weather_forecast["temperatureMax"],
                    weather_forecast["temperatureMin"],
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
        if weather_forecast['rc'] != 0:
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
        weekday_arr=("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
        if weather_forecast["time_difference"]==0:
            day_string="heute"
        elif weather_forecast["time_difference"]==1:
            day_string="morgen"
        else:
            temp_day=datetime.today().weekday()+weather_forecast["time_difference"]
            if temp_day <= 7:
                day_string="am " + weather_forecast["weekday"]
            else:
                day_string="am " + weather_forecast["requested_date"]
            
        return day_string
