# -*- encoding: utf-8 -*-

import datetime
from hermes_python.ffi.ontology import Grain
from enum import Enum

class DateType(Enum):
    FIXED = "fixed"
    INTERVAL = "interval"
    
class ForecastType(Enum):
    FULL = "full"
    TEMPERATURE = "temperature"
    ITEM = "item"
    CONDITION = "condition"

class WeatherRequest:
    
    def __init__(self, date_type, grain, request_date, forecast_type):
        self.date_type = date_type
        self.grain = grain
        self.request_date = request_date
        self.location = ""
        self.start_time = "00:00:00"
        self.end_time = "00:00:00"
        self.requested = ""
        self.forecast_type = forecast_type
    
    def __str__(self): 
        return "(" + str(self.forecast_type) + ", " + str(self.date_type) + ", " + \
               str(self.grain) + ", " + self.string_date + ", " + str(self.start_time) + \
               ", " + str(self.end_time) + ", " + self.location + ", " + self.requested + ")"
    
    @property
    def grain(self):
        return self.__grain
    @grain.setter
    def grain(self, val):
        if type(val) is Grain:
            self.__grain = val
    @property
    def date_type(self):
        return self.__date_type
    @date_type.setter
    def date_type(self, val):
        if type(val) is DateType:
            self.__date_type = val
    @property
    def forecast_type(self):
        return self.__forecast_type
    @forecast_type.setter
    def forecast_type(self, val):
        if type(val) is ForecastType:
            self.__forecast_type = val
    @property
    def request_date(self):
        return self.__request_date
    @request_date.setter
    def request_date(self, val):
        print(type(val))
        if type(val) is datetime.date:
            self.__request_date = val
        elif type(val) is str:
            self.__request_date = datetime.datetime.strptime(val, "%Y-%m-%d").date()
    @property
    def start_time(self):
        return self.__start_time
    @start_time.setter
    def start_time(self, val):
        if type(val) is datetime.time:
            self.__start_time = val
        elif type(val) is str:
            self.__start_time = datetime.datetime.strptime(val, "%H:%M:%S").time()
    @property
    def end_time(self):
        return self.__end_time
    @end_time.setter
    def end_time(self, val):
        if type(val) is datetime.time:
            self.__end_time = val
        elif type(val) is str:
            self.__end_time = datetime.datetime.strptime(val, "%H:%M:%S").time()

    
    @property
    def weekday(self):
        return self.request_date.strftime("%A")
        
    @property
    def readable_date(self):
        return self.request_date.strftime("%d. %B")
        
    @property
    def string_date(self):
        return self.request_date.strftime("%Y-%m-%d")
        
    @property
    def string_start_time(self):
        return self.start_time.strftime("%H:%M:%S")
        
    @property
    def string_end_time(self):
        return self.end_time.strftime("%H:%M:%S")
    @property
    def readable_start_time(self):
        return self.start_time.strftime("%H:%M")
        
    @property
    def readable_end_time(self):
        return self.end_time.strftime("%H:%M")
        
    @property
    def time_difference(self):
        return (self.request_date-datetime.date.today()).days
        
    @property
    def output_day(self):
        """
        Takes the time difference to today to figure out which day it will use in the response
        """
        if self.time_difference == 0:
            return "heute"
        elif self.time_difference == 1:
            return "morgen"
        else:
            temp_day=datetime.today().weekday()+self.time_difference
            if temp_day < 7:
                return "am " + self.weekday
            elif temp_day < 14:
                return "nächste Woche " + self.weekday
        return "am " + self.readable_date
            
    @property
    def output_location(self):
        return " in {0}".format(self.location) if self.location else ""
