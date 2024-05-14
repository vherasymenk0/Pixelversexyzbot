| Features                            | Functionality        |   
|-------------------------------------|----------------------|
| **Multithreading**                  | **Auto click**       |
| **Binding a proxy to a session**    | **Auto upgrade pet** |
| **Random unique mobile user agent** |                      |
| **Support pyrogram .session**       |                      |
---
## Settings via .env file
| Property                 | Description                                                                           |
|--------------------------|---------------------------------------------------------------------------------------|
| **API_ID / API_HASH**    | Platform data from which to launch a Telegram session (stock - Android)               |
| **SECRET_KEY**           | Key for creating a secret hash                                                        |
| **USE_PROXY_FROM_FILE**  | Whether to use proxy from the `bot/config/proxies.txt` file (True / False)            |
| **MIN_AVAILABLE_ENERGY** | Minimum amount of available energy, upon reaching which there will be a delay (eg 10) |
| **RANDOM_CLICKS_COUNT**  | Random number of taps (eg 5,9)                                                        |
| **SLEEP_BETWEEN_TAP**    | Random delay between taps in seconds (eg 7,15)                                        |
| **AUTO_UPGRADE**         | Should the pet be improved (true/false)                                               |
---
## Installation 

1. Copy .env-example to .env
2. Specify your **API_ID** and **API_HASH**
3. Fill **bot_info** in **bot/core/bot_info.py** before startup

4. Execute in the terminal
```shell
~bot/ >>> python -m venv venv
~bot/ >>> source venv/bin/activate
~bot/ >>> pip install -r requirements.txt
~bot/ >>> python main.py
```

#### Also for quick launch you can use arguments, for example:
```shell
~bot/ >>> python main.py --action (1/2)
# Or
~bot/ >>> python main.py -a (1/2)

#1 - Create session
#2 - Run clicker
```
