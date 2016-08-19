# Epic War Bot

[![Build Status](https://travis-ci.org/eigenein/epicwar.svg?branch=master)](https://travis-ci.org/eigenein/epicwar)

## Features

* Upgrades buildings.
* Cleans up extended areas.
* Upgrades units.
* Collects resources from production buildings.
* Sends mana to alliance members.
* Collects mana.
* Sends help to alliance members.
* Asks alliance members for help.
* Collects help from alliance members.
* Activates alliance daily gift.
* Collects alliance daily gift.
* Simulates user behavior by making random delays between requests.
* Participates in well-known bastion battles.
* Spins event roulette.
* Sends Telegram notification.

## Scripts

|File||
|---|---|
|`bot.py`|Runs the bot once|
|`epicwar.ipynb`|Used to investigate game requests|
|`tools/command-log.py`|Used to investigate a battle command log|
|`tools/generate-library.py`|Used to generate static library content|

## Configuring

### Environment Variables

|Variable||
|---|---|
|`EPIC_WAR_TELEGRAM_TOKEN`|Telegram bot token|
|`EPIC_WAR_TELEGRAM_CHAT_ID`|Telegram chat ID|

### Updating Library

Use "Network" tab in a browser to look for a link like `https://epicwar.cdnvideo.ru/vk/v0294/lib/lib.json.gz`.
