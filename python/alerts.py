#!/usr/bin/python3
# coding: utf8
import logging

import requests
import json
from discord import Webhook, RequestsWebhookAdapter

class alert_module:
    def __init__(self):
        configFile = '/config/config.json'
        with open(configFile,'r') as of:
            self.data = json.load(of)

    def discord(self, alert_msg=""):
        alert_info = self.data['Alerts']
        for alert_data in alert_info:
            if alert_data['Alerts-Enabled'] == True:
                webhook = Webhook.from_url(alert_data['Discord-Webhook'], adapter=RequestsWebhookAdapter())

                try:
                    webhook.send(alert_msg)
                except Exception as err:
                    logging.critical(f'Discord message not sent issue: {err}')

