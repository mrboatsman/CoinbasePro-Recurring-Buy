import plotly.graph_objects as go
from plotly.subplots import make_subplots
from storage_handler import Storage
import schedule
import datetime
import time
import logging


logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S')

def generate_plot():
    handler = Storage()
    my_order_history = handler.get_history()

    accumulated_value = list()
    date_axis = list()
    invested = list()
    bitcoin_price = list()
    accumulated_coins = 0

    for order in my_order_history:
        current_price = order.fiat_cost / order.amount_coins
        bitcoin_price.append(current_price)
        accumulated_coins = accumulated_coins + order.amount_coins
        accumulated_value.append(accumulated_coins * current_price)

        invested.append(next(reversed(invested), 0) + order.fiat_cost)
        date_axis.append(order.timestamp)

    # Create figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Add traces
    fig.add_trace(
        go.Scatter(x=date_axis, y=accumulated_value, name="Value")
    )

    fig.add_trace(
        go.Scatter(x=date_axis, y=invested, name="Invested Euro")
    )

    fig.add_trace(
        go.Scatter(x=date_axis, y=bitcoin_price, name="BTC/EUR"),
        secondary_y=True,
    )

    # Add figure title
    fig.update_layout(
        title_text=f"DCA Coinbase Pro with smash buys<br>"
                   f"Generated:{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # Set x-axis title
    fig.update_xaxes(title_text="Date")

    # Set y-axes titles
    fig.update_yaxes(title_text="<b>Euro</b>", side='right')

    fig.update_yaxes(title_text="<b>BTC/EUR</b>",
                     secondary_y=True, side='left')

    logging.info("Generating DCA plot")
    fig.write_html("/public_html/index.html")


generate_plot()
schedule.every(5).hours.do(generate_plot)

while True:
    schedule.run_pending()
    time.sleep(1)
