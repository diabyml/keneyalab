# Backup And Restore Guide

This guide explains how to use the encrypted backup system for Keneya Lab.
Backups include the PostgreSQL database and MinIO uploads such as lab logos,
result images, and report assets.

## 1. Configure Backups

In the root `.env`, set these values:

```env
BACKUP_HOST_PATH=./backups
BACKUP_ENCRYPTION_PASSPHRASE=change-this-long-passphrase
BACKUP_RUN_HOUR=2
BACKUP_RUN_MINUTE=0
BACKUP_RUN_ON_START=false
TZ=Africa/Bamako
```

Before real use, replace `BACKUP_ENCRYPTION_PASSPHRASE` with a long secret.
Keep that secret outside the server. If you lose it, encrypted backups cannot
be restored.

Create the backup folder:

```bash
mkdir -p backups
chmod 700 backups
```

## 2. Start Automatic Backups

Start the scheduled backup service:

```bash
docker compose -f compose.yml -f compose.backup.yml up -d --build backup
```

View backup logs:

```bash
docker compose -f compose.yml -f compose.backup.yml logs -f backup
```

By default, backups run daily at `02:00` in the configured timezone.

## 3. Run A Manual Backup

Run a one-off backup at any time:

```bash
docker compose -f compose.yml -f compose.backup.yml run --rm backup \
  /usr/local/bin/keneyalab-backup/run-backup.sh
```

Backup files are written to:

- `backups/daily`: latest 14 daily encrypted backups.
- `backups/weekly`: latest 8 Sunday encrypted backups.

Archive names look like:

```text
keneyalab-YYYYMMDD-HHMMSS.tar.gz.gpg
```

## 4. Verify A Backup

Pick one archive and verify that it decrypts:

```bash
mkdir -p /tmp/keneyalab-restore-check
gpg --pinentry-mode loopback --decrypt backups/daily/keneyalab-YYYYMMDD-HHMMSS.tar.gz.gpg \
  > /tmp/keneyalab-restore-check/backup.tar.gz
tar -tzf /tmp/keneyalab-restore-check/backup.tar.gz | head
rm -rf /tmp/keneyalab-restore-check
```

You should see files such as:

```text
keneyalab-YYYYMMDD-HHMMSS/manifest.json
keneyalab-YYYYMMDD-HHMMSS/db.dump
keneyalab-YYYYMMDD-HHMMSS/minio/
```

## 5. Restore A Backup

Restore is destructive. It replaces the configured database and MinIO bucket.
Only restore after confirming you selected the correct archive.

Stop application services first:

```bash
docker compose stop backend frontend prestart
```

Run restore:

```bash
docker compose -f compose.yml -f compose.backup.yml run --rm backup \
  /usr/local/bin/keneyalab-backup/restore-backup.sh \
  /backups/daily/keneyalab-YYYYMMDD-HHMMSS.tar.gz.gpg --confirm
```

Restart the app:

```bash
docker compose up -d backend frontend prestart
```

Check status:

```bash
docker compose ps
docker compose logs backend
```

## 6. Operational Rules

- Copy encrypted backups off the machine regularly.
- Test restore on a disposable local stack before launch.
- Do another restore drill after major infrastructure changes.
- Do not keep the encryption passphrase only in `.env`.
- Never run `docker compose down -v` unless you intentionally want to delete
  Docker volumes.

## 7. Troubleshooting

If backup fails with a passphrase error, replace:

```env
BACKUP_ENCRYPTION_PASSPHRASE=change-this-long-passphrase
```

If PostgreSQL backup fails, check:

```bash
docker compose ps db
docker compose logs db
```

If MinIO backup fails, check:

```bash
docker compose ps minio minio-init
docker compose logs minio
docker compose logs minio-init
```

If the backup service is not running:

```bash
docker compose -f compose.yml -f compose.backup.yml ps backup
docker compose -f compose.yml -f compose.backup.yml logs backup
```
