# Minimal image for smoke-testing the CLI entrypoint (no GPU).
FROM debian:12-slim
RUN apt-get update && apt-get install -y --no-install-recommends bash ca-certificates \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/agi-cli
COPY agi /usr/local/bin/agi
RUN chmod +x /usr/local/bin/agi
ENV TERM=xterm-256color
CMD ["agi"]
