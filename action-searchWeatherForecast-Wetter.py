#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import configparser
from hermes_python.hermes import Hermes, MqttOptions
import io
from weather import Weather
import toml

import ptvsd

USERNAME_INTENTS = "daenara"
MQTT_BROKER_ADDRESS = "localhost:1883"
MQTT_USERNAME = None
MQTT_PASSWORD = None


def add_prefix(intent_name):
    return USERNAME_INTENTS + ":" + intent_name


def read_configuration_file():
    try:
        cp = configparser.ConfigParser()
        with io.open("config.ini", encoding="utf-8") as f:
            cp.read_file(f)
        return {section: {option_name: option for option_name, option in cp.items(section)}
                for section in cp.sections()}
    except (IOError, configparser.Error):
        return dict()


def intent_callback_weather(hermes, intent_message):
    hermes.publish_end_session(intent_message.session_id, weather.get_weather_forecast(intent_message))


def intent_callback_weather_condition(hermes, intent_message):
    hermes.publish_end_session(intent_message.session_id, weather.get_weather_forecast(intent_message))


def intent_callback_weather_temperature(hermes, intent_message):
    hermes.publish_end_session(intent_message.session_id, weather.get_weather_forecast(intent_message))

def intent_callback_weather_item(hermes, intent_message):
    hermes.publish_end_session(intent_message.session_id, weather.get_weather_forecast(intent_message))


if __name__ == "__main__":
    ptvsd.enable_attach()
    config = read_configuration_file()
    weather = Weather(config)

    snips_config = toml.load('/etc/snips.toml')
    if 'mqtt' in snips_config['snips-common'].keys():
        MQTT_BROKER_ADDRESS = snips_config['snips-common']['mqtt']
    if 'mqtt_username' in snips_config['snips-common'].keys():
        MQTT_USERNAME = snips_config['snips-common']['mqtt_username']
    if 'mqtt_password' in snips_config['snips-common'].keys():
        MQTT_PASSWORD = snips_config['snips-common']['mqtt_password']
    mqtt_opts = MqttOptions(username=MQTT_USERNAME, password=MQTT_PASSWORD, broker_address=MQTT_BROKER_ADDRESS)

    with Hermes(mqtt_options=mqtt_opts) as h:
        h.subscribe_intent(add_prefix("searchWeatherForecast"), intent_callback_weather)
        h.subscribe_intent(add_prefix("searchWeatherForecastCondition"), intent_callback_weather_condition)
        h.subscribe_intent(add_prefix("searchWeatherForecastTemperature"), intent_callback_weather_temperature)
        h.subscribe_intent(add_prefix("searchWeatherForecastItem"), intent_callback_weather_item)
        h.start()
