# Snips-Wetter ☀
This skill makes [Snips.ai](https://snips.ai/) say the weather. The weather
forecasts come from [OpenWeatherMap](https://openweathermap.org/).

## Found a bug?
Just open an issue and supply me with the sentence that produced the bug. If you know where to find 
the output of the snips skill server you can also add that, might help me find the bug faster.

## Installation
**Important:** The following instructions assume that [Snips](https://snips.gitbook.io/documentation/snips-basics) is
already configured and running on your device. [SAM](https://snips.gitbook.io/getting-started/installation) should
also already be set up and connected to your device and your account.
1. In the German [skill store](https://console.snips.ai/) add the
skill `Wetter` (by daenara; [this](https://console.snips.ai/store/de/skill_Ya9gVa0eg0o)) to
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
    You will be asked to enter a few values:
	- `detail`
		Snips-Wetter provides more detailed weather reports if this is True
    - `openweathermap_api_key`
        Here you (copy and) paste the key you generated before.
    - `city`
        This is the location that is used when no location has been said, e.g. Berlin (without quotes).
	- `zipcode`
		Zipciode of your city (more precice in case of big cities)
	- `country`
		needed for the api to find a city by zipcode`
	- `lat` and `lon`
		latitude and longitude of where you live are the most precize way to get the weather
    
    This data is stored on your device.
    
5. To update the values simply run
    ```bash
    sam install skills
    ```

## Usage
Just ask for a weather report, a specific condition, an item or a temperature, Snips-Wetter should be able to answer.
Some aspects might only yield a general answer, thought. Since the free API of OpenWeatherMap only has data for 5 days, anything farther away will not be answered.

### Example sentences
- *Kannst du mir sagen wie das Wetter ist?*
- *Ich möchte das Wetter in Berlin wissen.*
- *Regnet es in Frankfurt?*
- *Wie viel Grad hat es draußen?*
- *Brauche ich morgen einen Regenschirm?*
- *Brauche ich am Sonntag Sonnencreme?*

## Todo
- Add another forecast provider
- Force snips to adhere to my definition of morning, midday, evening and night
- Get snips to answer questions containing the above (right now it answers only in general)
- Add more specified answers when asking about a certain temperature (*Wie warm ist es draußen?* oder *Ist es heute kalt*)
- Fully document this code
