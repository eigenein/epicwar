# Epic War Bot [![Build Status](https://travis-ci.org/eigenein/epicwar.svg?branch=master)](https://travis-ci.org/eigenein/epicwar)

## Features

* 👷 Multiple accounts.
* 👷 Upgrades buildings.
* 👷 Cleans up extended areas.
* 👷 Upgrades units.
* 🍔 Collects resources from production buildings.
* 🍬 Sends mana to alliance members.
* 🍬 Collects mana.
* 🍬 Activates alliance daily gift.
* 🍬 Collects alliance daily gift.
* 🆘 Sends help to alliance members.
* 🆘 Collects help from alliance members.
* 👦 Simulates user behavior by making random delays between requests.
* 🏆 Participates in known bastion battles.
* 🏆 Participates in PvP battles and uses heroes.
* 🎲 Spins event roulette.
* ✔️ Farms Random War tasks.
* 📨 Sends Telegram notification.

## Running

See `example.ini` for a configuration file example. Run the bot with `bot.py run --config config.ini`.

## Updating library

Use Web Inspector to look for a link like `https://epicwar.cdnvideo.ru/vk/v0294/lib/lib.json.gz`. Then pass it to `tools/generate-library.py`, commit and push changes.

## Adding new resource, building and unit types

* Update corresponding class in `epicbot.enums`.
* Update `Sets` class.

## Helper scripts

|File||
|---|---|
|`tools/command-log.py`|Used to investigate a battle command log|
|`tools/generate-library.py`|Used to generate static library content|
