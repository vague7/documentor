# Backing-up Chat History in MongoDB Atlas

This short guide explains two production-safe ways to protect the `messages` collection when you opt into the
`mongo` history backend.

---

## 1. Atlas Snapshots (Recommended)

1. In the Atlas UI, open **Backup** → **Policies**.
2. Create a new snapshot policy, e.g.:
   * Frequency: *Hourly* – keep 48
   * Daily: keep 7
   * Weekly: keep 4
   * Monthly: keep 3
3. Attach the policy to the cluster that stores the **documentor** database.
4. Verify backups via **Restore Jobs**.

Atlas snapshots are block-level and incremental – restores are full-cluster but
can be spun up into a temporary cluster for point-in-time recovery.

---

## 2. `mongodump` / `mongorestore`

Use when you want collection-level backups or to export data outside Atlas.

```bash
# Dump only the messages collection
mongodump \
  --uri "$MONGODB_URI" \
  --db documentor \
  --collection messages \
  --gzip --archive=messages_$(date +%F).gz
```

Automate the command via cron and rotate old archives using `logrotate` or a
simple `find -mtime` script.

Restore:
```bash
mongorestore --uri "$MONGODB_URI" --gzip --archive=messages_2025-06-30.gz
```

---

## 3. Disaster-Recovery Checklist

* [ ] Snapshot policy enabled and tested.
* [ ] `init_indexes.py` scripted in CI so restored clusters are immediately usable.
* [ ] Application secrets (`MONGODB_URI`) stored in your secret-manager.
* [ ] Run `mongotop` or Atlas metrics to ensure indexing keeps write latency low
      after large restores. 