# Coinbase Pro Recurring Buy Bot

Have you ever wanted to automate recurring purchases via Coinbase Pro instead of Coinbase? I did too, so I built a Bot to do it! The Bot can be setup to make recurring purchases weekly or every X number of days/seconds. Funds can be automatically added from your default funding account in Coinbase Pro or from Coinbase. Notifications about buys and funding can be sent to a Discord channel via webhook.

Built in Python and includes the following modules:<br />
CoinbasePro by [Alex Contryman](https://github.com/acontry/coinbasepro)<br />
Discord by [Rapptz](https://github.com/Rapptz/discord.py)<br />
Schedule by [Dan Bader](https://github.com/dbader/schedule)<br />

## Coinbase Pro Recurring Buy Config

The `config.json` file is where all settings come from. The Bot checks for the config file at `/config/config.json` when it starts up.

Example config file available here: https://github.com/queball99/CoinbasePro-Recurring-Buy/blob/main/config.example.json

To get started copy the `config.example.json` file to a folder that will be mapped to a Docker volume. Rename the file to `config.json` and edit the settings based on your needs. See Configuration Options below.

[Creating a Coinbase Pro API Key](https://help.coinbase.com/en/pro/other-topics/api/how-do-i-create-an-api-key-for-coinbase-pro)<br />
[Creating a Discord Webhook](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks)

The Coinbase Pro API Key will need a minimum of 'View' and 'Trade' permissions. If you want to enable Auto-Funding you will also need to grant it 'Transfer' permissions.

### Configuration File Options

| Section | Type | Description | Required |
| :---- | :--- | :--- | :--- |
| | | | |
| **API** | | | |
| Key | String | API Key from Coinbase Pro | Yes |
| Secret | String | API Secret from Coinbase Pro | Yes |
| Passphrase | String | API Passphrase from Coinbase Pro | Yes |
| API-URL | String | Coinbase Pro API URL You can use the production or sandbox URL.<br />Available Options: `https://api.pro.coinbase.com` or `https://api-public.sandbox.pro.coinbase.com` | Yes |
| | | |
| **Schedule** |  |  |  |
| Scheduled-Run | String | How often should the recurring buy be run.<br />Available Options: `seconds`, `days`, `weekday` | Yes |
| Day | String | Day of the week to make the recurring buy.<br />Available Options: `sunday`, `monday`, `tuesday`, `wednesday`, `thursday`, `friday`, `saturday` | If Scheduled-Run is set to `weekday` |
| Time | String | The time to make the recurring buy. Specified in 24hr time as `HH:MM`. | If Scheduled-Run is set to `weekday` or `days`. |
| Repeat-Time | Integer | Delay between runs. Will be X days or X seconds depending on if Scheduled-Run is set to `days` or `seconds`. | If Scheduled-Run is set to `days` or `seconds` |
| | | |
| **Funding** |  |  |  |
| Enable-Funding | Boolean | Enable automatic funding.<br />Available Options: `true` or `false` | Yes |
| Currency | String | The currency to fund your account with.<br />Examples: `USD`, `GBP`, `EUR` | If Enable-Funding is set to `true` |
| Max-Fund | Integer | The maximum amount of currency you want to allow the bot to fund at one time. | If Enable-Funding is set to `true` |
| Fund-Source | String | The source to fund your Coinbase Pro account from to make the purchase.<br />Available Options:<br />`default` will fund from your primary Banking account in Coinbase Pro.<br />`coinbase` will transfer currency from your Coinbase portfolio. | If Enable-Funding is set to `true` |
| | | |
| **Crypto** |  |  |  |
| Buy-Pair | String | Crypto buy pair in Coinbase Pro.<br />Examples: `BTC-USD`, `ETH-USD`, `BTC-GBP`, etc. | Yes |
| Buy-Amount | Integer | The amount of crypto to buy, specified in your currency.<br />Example: Specifying `20` and `BTC-USD` will buy 20 USD worth of BTC. | Yes |
| | | | |
| **Alerts** |  |  |  |
| Alerts-Enabled | Boolean | Enables sending buy and funding alerts to Discord. | Yes |
| Discord-Webhook | String | The webhook URL you create in your Discord server. | If Alerts-Enabled is set to `true` |
|                 |        |                                        |          |
| **Withdraw**    |        |                                        | No       |
| Currency        | String | Which crypto cyrrency to withdraw      | Yes      |
| Fees            | Number | The transaction fees which is common   | Yes      |
| Threshold       | Number | The limit before a withdraw shall be executed | Yes |
| Address         | String | The receiver address of the funds      | Yes      |

### Withdraw
Use with caution! in Coinbase Pro activate address [whitelisting](https://help.coinbase.com/en/pro/managing-my-account/other/how-does-whitelisting-in-the-address-book-work)
before use this option. Activate an API with `Transfer` permision. 


## Discord Alerts

You can have alerts about funding and buys sent to Discord via a Webhook. See this [Discord support article](https://support.discord.com/hc/en-us/articles/228383668-Intro-to-Webhooks) for how to setup a Webhook.

## Docker Container

### Supported Architectures

| Architecture |
| :----: |
| x86-64 |

### Version Tags

| Tag | Description |
| :---- | --- |
| latest | Latest stable release |
| development | New features will be added and tested here |

### Docker Compose

Compatible with docker-compose v2 schemas.

```yaml
---
version: "2.1"
services:
  coinbase-pro-buy:
    build: 
      context: ./
      dockerfile: Dockerfile
    container_name: coinbase-pro-recurring-buy
    environment:
      - TZ=Europe/Amsterdam
      - DEBUG=True
    volumes:
      - ./config:/config
    restart: unless-stopped

```

### Docker Compose with Plotply
```yaml
---
version: "2.1"
services:
  coinbase-pro-buy:
    build: 
      context: ./
      dockerfile: Dockerfile
    container_name: coinbase-pro-recurring-buy
    environment:
      - TZ=Europe/Amsterdam
      - DEBUG=True
    volumes:
      - ./config:/config
      - storage:/storage
    depends_on:
      - "plot-generation"
    restart: unless-stopped

  plot-generation:
    build: 
      context: ./
      dockerfile: Dockerfile_plot
    container_name: coinbase-pro-plot-generate
    environment:
      - TZ=Europe/Amsterdam
    volumes:
      - storage:/storage
      - public_html:/public_html
    restart: unless-stopped

  nginx:
    image: nginx:latest
    container_name: coinbase-pro-plot-hosting
    ports:
      - 1480:80
    volumes:
       - public_html:/usr/share/nginx/html
    depends_on:
      - "plot-generation"

volumes:
  storage:
  public_html:
```

### Docker CLI

```bash
docker run -d \
  --name=coinbase-pro-recurring-buy \
  -e TZ=America/New_York \
  -v /path/to/folder:/config \
  --restart unless-stopped \
  queball/coinbase-pro-recurring-buy
```

### Parameters

| Parameter | Function |
| :---: | --- |
| TZ | Specify a timezone to use. Default is `America/New_York` |

## Updating The Container

### Docker Compose

* Update all images: `docker-compose pull`
  * or update a single image: `docker-compose pull coinbase-pro-recurring-buy`
* Let compose update all containers as necessary: `docker-compose up -d`
  * or update a single container: `docker-compose up -d coinbase-pro-recurring-buy`
* You can also remove the old dangling images: `docker image prune`

### Docker Run

* Update the image: `docker pull queball/coinbase-pro-recurring-buy`
* Stop the container: `docker stop coinbase-pro-recurring-buy`
* Delete the container: `docker rm coinbase-pro-recurring-buy`
* Recreate a new container with the same docker run parameters from above. Your `/config` folder containing the config.json folder will not be changed.
* You can remove old images with: `docker image prune`

## Building Locally

If you want to build the container locally:

```bash
git clone https://github.com/queball99/CoinbasePro-Recurring-Buy.git
cd CoinbasePro-Recurring-Buy
docker build .
```
