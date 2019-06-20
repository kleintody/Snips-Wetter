# Snips-Wetter ☀
This skill makes [Snips.ai](https://snips.ai/) say the weather. The weather
forecasts come from [OpenWeatherMap](https://openweathermap.org/).

## Installation
**Important:** The following instructions assume that [Snips](https://snips.gitbook.io/documentation/snips-basics) is
already configured and running on your device. [SAM](https://snips.gitbook.io/getting-started/installation) should
also already be set up and connected to your device and your account.
1. In the German [skill store](https://console.snips.ai/) add the
skill `Wetter` (by domi; [this](https://console.snips.ai/app-editor/bundle_7ZYEq522Ang)) to
your *German* assistant.

2. Go to the [OpenWeatherMap](https://openweathermap.org/) website and create
a [new account](https://home.openweathermap.org/users/sign_up),
or [sign in](https://home.openweathermap.org/users/sign_in) if you already have one.

3. In "My Home" go to the section "[API keys](https://home.openweathermap.org/api_keys)" and generate a new key.
Copy this one.

4. In the console execute the following command:
    ```bash
    sam install assistant
    ```
    You will be asked to enter two values:
    - `openweathermap_api_key`
        Here you (copy and) paste the key you generated before.
    - `default_city`
        This is the location that is used when no location has been said, e.g. Berlin (without quotes).
    
    This data is stored on your device.
    
5. To update the values simply run
    ```bash
    sam install skills
    ```

## Usage
At the moment you can ask for the current weather, the temperature and the weather condition as well as the weather for a few days in advance.

### Example sentences
- *Kannst du mir sagen wie das Wetter ist?*
- *Ich möchte das Wetter in Berlin wissen.*
- *Regnet es in Frankfurt?*
- *Wie viel Grad hat es draußen?*

## Todo
- Get it to give the weather for morning, midday or evening for specific days
- Output the temperature and or weather at a specific hour (forecast already done)
- More complete weather report for the day (split up in morning, midday, evening instead of one condensed forecast for the whole day)
- ~~Leave out the location if not specified in the question~~

