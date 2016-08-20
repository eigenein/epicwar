# Epic War Bot

[![Build Status](https://travis-ci.org/eigenein/epicwar.svg?branch=master)](https://travis-ci.org/eigenein/epicwar)

## Features

* 👷 Upgrades buildings.
* 👷 Cleans up extended areas.
* 👷 Upgrades units.
* 🍔 Collects resources from production buildings.
* 🍬 Sends mana to alliance members.
* 🍬 Collects mana.
* 🍬 Activates alliance daily gift.
* 🍬 Collects alliance daily gift.
* 🆘 Sends help to alliance members.
* 🆘 Asks alliance members for help.
* 🆘 Collects help from alliance members.
* 👦 Simulates user behavior by making random delays between requests.
* 🏆 Participates in known bastion battles.
* 🏆 Participates in PvP battles.
* 🎲 Spins event roulette.
* 📨 Sends Telegram notification.

## Scripts

|File||
|---|---|
|`bot.py`|Runs the bot once|
|`epicwar.ipynb`|Used to investigate game requests|
|`tools/command-log.py`|Used to investigate a battle command log|
|`tools/generate-library.py`|Used to generate static library content|

## Configuring

### Environment variables

|Variable||
|---|---|
|`EPIC_WAR_TELEGRAM_TOKEN`|Telegram bot token|
|`EPIC_WAR_TELEGRAM_CHAT_ID`|Telegram chat ID|

### Updating library

Use "Network" tab in a browser to look for a link like `https://epicwar.cdnvideo.ru/vk/v0294/lib/lib.json.gz`.

### Adding new resource, building and unit types

* Update corresponding class in `epicbot.enums`.
* Remember to update class methods.
