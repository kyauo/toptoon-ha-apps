FROM ghcr.io/home-assistant/base:lastest
RUN apk add --no-cache python3 py3-pip tzdata \
    && python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir requests
COPY run.sh /run.sh
COPY bot.py /bot.py
RUN chmod a+x /run.sh
CMD ["/run.sh"]
