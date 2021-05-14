#!/usr/bin/python3

import os, sys
import json
import coinbasepro, schedule, time
import settings

if os.path.exists("/config/config.json"):

    settings = settings.settings()

    api_settings = settings.api()
    schedule_settings = settings.schedule()
    funding_settings = settings.funding()
    crypto_settings = settings.crypto()

    for api in api_settings:
        key = api['Key']
        b64secret = api['Secret']
        passphrase = api['Passphrase']
        apiurl = api['API-URL']

    for the_schedule in schedule_settings:
        run_day = the_schedule['Day']
        run_time = the_schedule['Time']
        repeat_time = the_schedule['Repeat-Time']
        run_every = the_schedule['Environment']

    for funding in funding_settings:
        enable_funding = funding['Enable-Funding']
        currency = funding['Currency']
        max_fund = funding['Max-Fund']
        fund_source = funding['Fund-Source']

    auth_client = coinbasepro.AuthenticatedClient(key, b64secret, passphrase, api_url=apiurl)

    def check_funds():
        account_data = auth_client.get_accounts()
        for account in account_data:
            if account['currency'] == currency:
                currency_balance = round(account['balance'])
                return currency_balance

    def get_funding_account():
        if fund_source == "default":
            payment_methods = auth_client.get_payment_methods()
            for payment in payment_methods:
                if payment['primary_buy'] == True:
                    payment_id = payment['id']
        elif fund_source == "coinbase":
            payment_methods = auth_client.get_coinbase_accounts()
            for payment in payment_methods:
                if ((payment['currency'] == "USD") and (payment['balance'] > 0)):
                    payment_id = payment['id']
        else:
            payment_id = "Error"
        
        return payment_id

    def add_funds(buy_total, current_funds):
        if buy_total > max_fund:
            error_msg = "Error: Total crypto cost is %s %s but max funding is set to %s %s. Unable to complete purchase.\nPlease check your config file." % (buy_total, currency, max_fund, currency)
            return ("Error", error_msg)
        else:
            fund_amount = buy_total - current_funds
            print("Your balance is %s %s, a deposit of %s %s will be made using your selected payment account." % (current_funds, currency, fund_amount, currency))
            payment_id = get_funding_account()
            if payment_id == "Error":
                error_msg = "Unable to determine payment method."
                return ("Error", error_msg)
            else:
                if fund_source == "coinbase":
                    # Coinbase Deposit
                    deposit = auth_client.deposit_from_coinbase(amount=fund_amount, currency=currency, coinbase_account_id=payment_id)
                    return ("Success", deposit)
                elif fund_source == "default":
                    # Default Deposit
                    deposit = auth_client.deposit(amount=fund_amount, currency=currency, payment_method_id=payment_id)
                    time.sleep(10)
                    return ("Success", deposit)
                else:
                    error_msg = "Something went wrong attempting to add funds."
                    return ("Error", error_msg)

    # Function to perform the buy
    def init_buy():
        for crypto in crypto_settings:
            buy_pair = crypto['Buy-Pair']
            buy_amount = crypto['Buy-Amount']
            print("Initiating buy of %s %s of %s..." % (buy_amount, currency, buy_pair))
            buy = auth_client.place_market_order(product_id=buy_pair, side="buy", funds=buy_amount)
            # Get Order details
            order_id = buy['id']
            order_details = auth_client.get_order(order_id=order_id)
            crypto_bought = order_details['filled_size']
            buy_completed = order_details['done_at']
            print("You bought %s of %s" % (crypto_bought, buy_pair))

    def recurring_buy():
        buy_total = 0
        for crypto in crypto_settings:
            buy_total += crypto['Buy-Amount']

        current_funds = check_funds()

        if current_funds >= buy_total:
            init_buy()
        elif current_funds < buy_total:
            if enable_funding == True:
                result = add_funds(buy_total, current_funds)
                if result[0] == "Error":
                    print(result[1])
                elif result[0] == "Success":
                    init_buy()
                else:
                    print("Something went wrong.")
            elif enable_funding != True:
                print("Insufficient funds to make purchases.")
                print("Please deposit at least %s %s into your account" % (buy_total, currency))       
    
    if run_every == "seconds":
        # Run every X seconds (mainly for testing purposes)
        schedule.every(repeat_time).seconds.do(recurring_buy)
    elif run_every == "days":
        # Run every X days at specified run time
        schedule.every(repeat_time).days.at(run_time).do(recurring_buy)
    elif run_every == "weekday":
        # Run every specified weekday at run time
        getattr(schedule.every(), run_day).at(run_time).do(recurring_buy)
    else:
        print("Unable to determine run type. Please check config...")
    
    while True:
        schedule.run_pending()
        time.sleep(1)
else:
    print("No config file found at '/config/config.json'. Please update your config file.")