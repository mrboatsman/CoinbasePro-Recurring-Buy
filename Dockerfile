# syntax=docker/dockerfile:1

FROM python:3

WORKDIR /app
RUN pip3 install git+https://github.com/mrboatsman/coinbasepro.git
RUN pip3 install schedule
RUN pip3 install discord
COPY ./python/ .

ENV TZ="America/New_York"

VOLUME [ "/config", "/storage" ]

CMD python3 ./recurring-buy.py

