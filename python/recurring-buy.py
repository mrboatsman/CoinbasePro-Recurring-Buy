#!/usr/bin/python3

import math
import coinbasepro
import coinbasepro.exceptions
import schedule
import time
import settings
import alerts as send_alert
import logging
import os
from storage_handler import Storage, Order

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

if os.path.exists("/config/config.json"):
    logging.debug('Reading settings from config file')
    general_settings = settings.settings()
    send_alert = send_alert.alert_module()

    api_settings = general_settings.api()
    schedule_settings = general_settings.schedule()

    for api in api_settings:
        key = api['Key']
        b64secret = api['Secret']
        passphrase = api['Passphrase']
        apiurl = api['API-URL']

    for the_schedule in schedule_settings:
        run_day = the_schedule['Day']
        run_time = the_schedule['Time']
        repeat_time = the_schedule['Repeat-Time']
        run_every = the_schedule['Scheduled-Run']

    storage = Storage()
    if not storage.synced():
        logging.info("Syncing order history, this can take a while.")
        auth_client = coinbasepro.AuthenticatedClient(key, b64secret,
                                                      passphrase,
                                                      api_url=apiurl)
        crypto_settings = general_settings.crypto()
        cryptos = [pair_list['Buy-Pair'] for pair_list in crypto_settings]

        for crypto in cryptos:
            orders = auth_client.get_orders(crypto, ['done'])
            for order in orders:
                if order.get('status') == 'done' and order.get('side') == 'buy'\
                        and order.get('product_id') == crypto:
                    fiat_cost = float(order.get('fill_fees')) + float(
                        order.get('executed_value'))
                    my_dummy = order.get('price')
                    storage.insert_order(
                        Order(order_id=order.get('id'),
                              fiat_cost=fiat_cost,
                              amount_coins=order.get('filled_size'),
                              fiat_currency=order.get('product_id').split('-')[1],
                              crypt_currency=order.get('product_id').split('-')[0],
                              price=0,     # For later implementation
                              timestamp=order.get('created_at')
                              )
                    )
        storage.update_sync()

    def check_funds(currency):
        auth_client = coinbasepro.AuthenticatedClient(key, b64secret,
                                                      passphrase,
                                                      api_url=apiurl)
        logging.debug('Checking funds')
        account_data = auth_client.get_accounts()
        for account in account_data:
            if account['currency'] == currency:
                currency_balance = math.floor(account['balance'])
                return currency_balance


    def get_funding_account(fund_amount, currency, fund_source):
        auth_client = coinbasepro.AuthenticatedClient(key, b64secret,
                                                      passphrase,
                                                      api_url=apiurl)

        if fund_source == "default":
            payment_methods = auth_client.get_payment_methods()
            for payment in payment_methods:
                if payment['primary_buy'] == True:
                    payment_id = payment['id']
        elif fund_source == "coinbase":
            payment_methods = auth_client.get_coinbase_accounts()
            for payment in payment_methods:
                if ((payment['currency'] == currency) and (
                        math.floor(payment['balance']) >= fund_amount)):
                    payment_id = payment['id']
                    break
                else:
                    payment_id = "Error"
        else:
            payment_id = "Error"
        return payment_id


    def add_funds(buy_total, current_funds, max_fund, fund_source, currency):
        logging.debug('Adding funds')
        auth_client = coinbasepro.AuthenticatedClient(key, b64secret,
                                                      passphrase,
                                                      api_url=apiurl)

        if buy_total > max_fund:
            error_msg = "Error: Total crypto cost is %s %s but max funding is set to %s %s. Unable to complete purchase.\nPlease check your config file." % (
                buy_total, currency, max_fund, currency)
            return ("Error", error_msg)
        else:
            fund_amount = buy_total - current_funds
            fund_msg = "Your balance is %s %s, a deposit of %s %s will be made using your selected payment account." % (
                current_funds, currency, fund_amount, currency)
            logging.info(fund_msg)
            send_alert.discord(fund_msg)
            payment_id = get_funding_account(fund_amount, currency, fund_source)
            if payment_id == "Error":
                error_msg = "Unable to determine payment method."
                return ("Error", error_msg)
            else:
                if fund_source == "coinbase":
                    # Coinbase Deposit
                    deposit = auth_client.deposit_from_coinbase(
                        amount=fund_amount, currency=currency,
                        coinbase_account_id=payment_id)
                    return ("Success", deposit)
                elif fund_source == "default":
                    # Default Deposit
                    deposit = auth_client.deposit(amount=fund_amount,
                                                  currency=currency,
                                                  payment_method_id=payment_id)
                    time.sleep(10)
                    return ("Success", deposit)
                else:
                    error_msg = "Something went wrong attempting to add funds."
                    return ("Error", error_msg)

    # Function to perform the buy
    def init_buy(crypto_settings, currency):
        auth_client = coinbasepro.AuthenticatedClient(key, b64secret,
                                                      passphrase,
                                                      api_url=apiurl)
        for crypto in crypto_settings:
            buy_pair = crypto['Buy-Pair']
            buy_amount = crypto['Buy-Amount']
            logging.info("Initiating buy of %s %s of %s..." % (
                buy_amount, currency, buy_pair))
            buy = auth_client.place_market_order(product_id=buy_pair,
                                                 side="buy", funds=buy_amount)
            # Get Order details
            order_id = buy['id']

            retry = True
            try_outs = 0
            while retry and try_outs < 5:
                """ Some times the coinbase pro order info api endpoint
                is slow to deliver order info"""
                try:
                    order_details = auth_client.get_order(order_id=order_id)

                except coinbasepro.exceptions.CoinbaseAPIError:
                    try_outs = try_outs + 1
                    logging.critical("Failed to get order info, retrying")
                    logging.debug(f"Retry order info request number {try_outs}")
                    retry = True
                    time.sleep(try_outs * try_outs)
                    if try_outs >= 5 and retry:
                        logging.critical(f"Cannot reach Coinbase order after "
                                         f"{try_outs} retries")
                        raise

                else:
                    crypto_bought = order_details['filled_size']
                    buy_message = "You bought %s of %s" % (
                        crypto_bought, buy_pair)
                    logging.info(buy_message)
                    send_alert.discord(buy_message)
                    storage_handler = Storage()
                    storage_handler.insert_order(
                        Order(order_id=order_id,
                              fiat_cost=order_details['fill_fees'] +
                                        order_details['executed_value'],
                              amount_coins=order_details['filled_size'],
                              fiat_currency
                              =order_details['product_id'].split('-')[1],
                              crypt_currency
                              =order_details['product_id'].split('-')[0],
                              price=order_details['price'],
                              timestamp=order_details['created_at']
                              )
                    )

                    retry = False

    def recurring_buy():

        recurring_buy_settings = settings.settings()
        funding_settings = recurring_buy_settings.funding()
        crypto_settings = recurring_buy_settings.crypto()

        for funding in funding_settings:
            enable_funding = funding['Enable-Funding']
            currency = funding['Currency']
            max_fund = funding['Max-Fund']
            fund_source = funding['Fund-Source']

        buy_total = 0
        for crypto in crypto_settings:
            buy_total += crypto['Buy-Amount']

        current_funds = check_funds(currency)

        if current_funds >= buy_total:
            init_buy(crypto_settings, currency)
        elif current_funds < buy_total:
            if enable_funding == True:
                result = add_funds(buy_total, current_funds, max_fund,
                                   fund_source, currency)
                if result[0] == "Error":
                    logging.critical(result[1])
                    send_alert.discord(result[1])
                elif result[0] == "Success":
                    init_buy(crypto_settings, currency)
                else:
                    fund_msg = "Something went wrong attempting to add funds to your account."
                    logging.critical(fund_msg)
                    send_alert.discord(fund_msg)
            elif enable_funding != True:
                funding_msg = "Unable to complete your Coinbase Pro purchase.\n\
            Insufficient funds to make purchase and Auto-Funding is not enabled.\n\
            Please deposit at least %s %s into your account" % (
                    buy_total, currency)
                logging.info(funding_msg)
                send_alert.discord(funding_msg)
                # print("Please deposit at least %s %s into your account" % (buy_total, currency))       


    if run_every == "seconds":
        # Run every X seconds (mainly for testing purposes)
        startupMsg = "Recurring Buy Bot Started!\nSchedule set for every %s seconds" % (
            repeat_time)
        schedule.every(repeat_time).seconds.do(recurring_buy)
        logging.info(startupMsg)
        send_alert.discord(startupMsg)
    elif run_every == "days":
        # Run every X days at specified run time
        startupMsg = "Recurring Buy Bot Started!\n" \
                     "Schedule set for every %s days at %s" % (
            repeat_time, run_time)
        schedule.every(repeat_time).days.at(run_time).do(recurring_buy)
        logging.info(startupMsg)
        send_alert.discord(startupMsg)
    elif run_every == "weekday":
        # Run every specified weekday at run time
        startupMsg = "Recurring Buy Bot Started!\n" \
                     "Schedule set for every %s at %s" % (run_day, run_time)
        getattr(schedule.every(), run_day).at(run_time).do(recurring_buy)
        logging.info(startupMsg)
        send_alert.discord(startupMsg)
    else:
        startupMsg = "Unable to determine run type. Please check config..."
        logging.info(startupMsg)
        send_alert.discord(startupMsg)

    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    logging.critical(
        "No config file found at '/config/config.json'. "
        "Please update your config file.")
