# -*- coding: utf-8 -*-
import requests
import datetime


class Weather:
    def __init__(self, config):
        self.fromtimestamp = datetime.datetime.fromtimestamp
        self.weather_api_base_url = "http://api.openweathermap.org/data/2.5"
        try:
            self.weather_api_key = config['openweathermap_api_key']
        except KeyError:
            self.weather_api_key = "XXXXXXXXXXXXXXXXXXXXX"
        try:
            self.default_city_name = config['default_city']
        except KeyError:
            self.default_city_name = "Berlin"
        try:
            self.units = config['units']
        except KeyError:
            self.units = "metric"

    def parse_open_weather_map_forecast_response(self, response, location):
        # Parse the output of Open Weather Map's forecast endpoint
        try:
            today = self.fromtimestamp(response["list"][0]["dt"]).day
            today_forecasts = list(
                filter(lambda forecast: self.fromtimestamp(forecast["dt"]).day == today, response["list"]))

            all_min = [x["main"]["temp_min"] for x in today_forecasts]
            all_max = [x["main"]["temp_max"] for x in today_forecasts]
            all_conditions = [x["weather"][0]["description"] for x in today_forecasts]
            rain = list(filter(lambda forecast: forecast["weather"][0]["main"] == "Rain", today_forecasts))
            snow = list(filter(lambda forecast: forecast["weather"][0]["main"] == "Snow", today_forecasts))

            return {
                "location": location,
                "inLocation": " in {0}".format(location) if location else "",
                "temperature": int(today_forecasts[0]["main"]["temp"]),
                "temperatureMin": int(min(all_min)),
                "temperatureMax": int(max(all_max)),
                "rain": len(rain) > 0,
                "snow": len(snow) > 0,
                "mainCondition": max(set(all_conditions), key=all_conditions.count).lower()
            }
        except KeyError:  # error 404 (locality not found or api key is wrong)
            return 2

    def get_weather_forecast(self, intentMessage):
        # Parse the query slots, and fetch the weather forecast from Open Weather Map's API
        locations = [intentMessage.slots.forecast_locality.first().value,
                     intentMessage.slots.forecast_country.first().value,
                     intentMessage.slots.forecast_region.first().value,
                     intentMessage.slots.forecast_geographical_poi.first().value,
                     self.default_city_name]
        location = [loc for loc in locations if loc is not None][0]
        print(location)
        """
        location = slots.get("forecast_locality", None) \
                   or slots.get("forecast_country", None) \
                   or slots.get("forecast_region", None) \
                   or slots.get("forecast_geographical_poi", None) \
                   or self.default_city_name
        """
        forecast_url = "{0}/forecast?q={1}&APPID={2}&units={3}&lang=de".format(
            self.weather_api_base_url, location, self.weather_api_key, self.units)
        try:
            r_forecast = requests.get(forecast_url)
            return self.parse_open_weather_map_forecast_response(r_forecast.json(), location)
        except (requests.exceptions.ConnectionError, ValueError):
            return 1  # Error: No internet connection

    @staticmethod
    def add_warning_if_needed(response, weather_forecast):
        if weather_forecast["rain"] and weather_forecast["mainCondition"] != "rain":
            response += ' Es könnte regnen.'
        if weather_forecast["snow"] and weather_forecast["mainCondition"] != "snow":
            response += ' Es könnte schneien.'
        return response

    def forecast(self, intentMessage):
        """
                Complete answer:
                    - condition
                    - current temperature
                    - max and min temperature
                    - warning about rain or snow if needed
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast == 1:
            response = ["Es ist leider kein Internet verfügbar.",
                        "Ich bin nicht mit dem Internet verbunden.",
                        "Es ist kein Internet vorhanden."]
        elif weather_forecast == 2:
            response = ["Ich kann das Wetter von diesem Ort nicht abrufen."]
        else:
            response = ("Wetter heute{1}: {0}. "
                        "Aktuelle Temperatur ist {2} Grad. "
                        "Höchsttemperatur: {3} Grad. "
                        "Tiefsttemperatur: {4} Grad.").format(
                weather_forecast["mainCondition"],
                weather_forecast["inLocation"],
                weather_forecast["temperature"],
                weather_forecast["temperatureMax"],
                weather_forecast["temperatureMin"]
            )
            response = self.add_warning_if_needed(response, weather_forecast)
        return response

    def forecast_condition(self, intentMessage):
        """
        Condition-focused answer:
            - condition
            - warning about rain or snow if needed
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast == 1:
            response = ["Es ist leider kein Internet verfügbar.",
                        "Ich bin nicht mit dem Internet verbunden.",
                        "Es ist kein Internet vorhanden."]
        elif weather_forecast == 2:
            response = ["Wetter konnte nicht abgerufen werden. Entweder gibt es den Ort nicht, oder der API-Schlüssel ist ungültig.",
                        "Fehler beim Abrufen. Entweder gibt es den Ort nicht, oder der API-Schlüssel ist ungültig."]
        else:
            response = "Wetter heute{1}: {0}.".format(
                weather_forecast["mainCondition"],
                weather_forecast["inLocation"]
            )
            response = self.add_warning_if_needed(response, weather_forecast)
        return response

    def forecast_temperature(self, intentMessage):
        """
        Temperature-focused answer:
            - current temperature
            - max and min temperature
        """
        weather_forecast = self.get_weather_forecast(intentMessage)
        if weather_forecast == 1:
            response = ["Es ist leider kein Internet verfügbar.",
                        "Ich bin nicht mit dem Internet verbunden.",
                        "Es ist kein Internet vorhanden."]
        elif weather_forecast == 2:
            response = ["Wetter konnte nicht abgerufen werden. Entweder gibt es den Ort nicht, oder der API-Schlüssel ist ungültig.",
                        "Fehler beim Abrufen. Entweder gibt es den Ort nicht, oder der API-Schlüssel ist ungültig."]
        else:
            response = ("{0} hat es aktuell {1} Grad. "
                        "Heute wird die Höchsttemperatur {2} Grad sein "
                        "und die Tiefsttemperatur {3} Grad.").format(
                weather_forecast["inLocation"],
                weather_forecast["temperature"],
                weather_forecast["temperatureMax"],
                weather_forecast["temperatureMin"]
            )
        return response
