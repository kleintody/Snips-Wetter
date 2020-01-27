# -*- encoding: utf-8 -*-
import datetime
import locale
from hermes_python.ontology.slot import InstantTimeValue, TimeIntervalValue
from hermes_python.ffi.ontology import Grain
from weather_logic import WeatherRequest, DateType, ForecastType, WeatherForecast, WeatherReport, Location
import copy

import ptvsd # used for debugging
class Weather:
    def __init__(self, config):
        try:
            self.detail = eval(config['global']['detail'])
        except KeyError:
            self.detail = False
        try:
            self.weather_api_key = config['secret']['openweathermap_api_key']
        except KeyError:
            self.weather_api_key = "XXXXXXXXXXXXXXXXXXXXX"
        try:
            self.location = Location(config['secret']['city'])
        except KeyError:
            self.location = Location("Berlin")
        try:
            zipcode = config['secret']['zipcode']
            country = config['secret']['country']
            self.location.set_zipcode(zipcode, country)
        except:
            pass
        try:
            lat = config['secret']['lat']
            lon = config['secret']['lon']
            self.location.set_lat_and_lon(lat, lon)
        except:
            pass
        try:
            self.units = config['global']['units']
        except KeyError:
            self.units = "metric"
        try:
            locale.setlocale(locale.LC_TIME, "de_DE.UTF-8")
        except locale.Error:
            print("That locale doesn't exist on the system")

    # function being called when snips detects an intent related to the weather
    def get_weather_forecast(self, intent_message):
        print("function: get_weather_forecast")
        requests = self.parse_intent_message(intent_message)
        response = ""
        #print(*requests, sep='\n')
        for request in requests:
            if request.location == "":
                forecast = WeatherForecast(self.units, self.location)
            else:
                forecast = WeatherForecast(self.units, Location(request.location))
            forecast.get_weather_from_open_weather_map(self.weather_api_key)
            response = response + WeatherReport(request, forecast).generate_report()
        
        return response

    # parse the query and return a list of WeatherRequests
    def parse_intent_message(self, intent_message):
        print("function: parse_intent_message")
        
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
        if intent_message.slots.forecast_start_date_time is not None and len(intent_message.slots.forecast_start_date_time) > 0:
            for start_date_time_slot in intent_message.slots.forecast_start_date_time:
                start_date_time = start_date_time_slot.slot_value.value
                new_request = None
                if type(start_date_time) is InstantTimeValue:
                    new_request = WeatherRequest(DateType.FIXED, start_date_time.grain, start_date_time.value.split(' ')[0], intent, self.detail)
                    if new_request.grain == Grain.SECOND:
                        new_request.grain = Grain.HOUR
                        new_request.start_time = start_date_time.value.split(' ')[1].split(".")[0]
                    elif new_request.grain == Grain.MINUTE:
                        new_request.grain = Grain.HOUR
                        new_request.start_time = start_date_time.value.split(' ')[1]
                    elif new_request.grain == Grain.HOUR:
                        new_request.start_time = start_date_time.value.split(' ')[1]
                elif type(start_date_time) is TimeIntervalValue:
                    new_request = WeatherRequest(DateType.INTERVAL, Grain.HOUR, start_date_time.from_date.split(' ')[0], intent, self.detail)
                    new_request.start_time = start_date_time.from_date.split(' ')[1]
                    if start_date_time.to_date == None:
                        new_request.end_time = "23:59:59"
                    else:
                        new_request.end_time = start_date_time.to_date.split(' ')[1]
                if new_request is not None:
                    new_request.time_specified = start_date_time_slot.raw_value
                    requests.append(new_request)
        else:
            requests.append(WeatherRequest(DateType.FIXED, Grain.DAY, datetime.date.today(), intent, self.detail))

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
