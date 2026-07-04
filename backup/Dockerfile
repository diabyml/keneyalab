FROM postgres:18

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gnupg \
    gzip \
    tar \
    tzdata \
    && curl -fsSL https://dl.min.io/client/mc/release/linux-amd64/mc \
      -o /usr/local/bin/mc \
    && chmod +x /usr/local/bin/mc \
    && rm -rf /var/lib/apt/lists/*

COPY backup/scripts/ /usr/local/bin/keneyalab-backup/
RUN chmod +x /usr/local/bin/keneyalab-backup/*.sh

CMD ["/usr/local/bin/keneyalab-backup/backup-loop.sh"]
