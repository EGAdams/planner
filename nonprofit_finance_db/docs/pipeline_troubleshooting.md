## PDF Import Pipeline Notes

- **Issue:** Ingestion crashed with `strptime() argument 1 must be str, not datetime.date` during duplicate detection.
  - **Cause:** Existing transactions retrieved from MySQL returned `datetime.date` objects, but the duplicate matcher expected ISO-formatted strings.
  - **Fix:** Normalize cached `transaction_date` values to `YYYY-MM-DD` strings in `ingestion/pipeline.py` when loading existing transactions.

- **Reminder:** When extending the pipeline, always verify that validated transactions remain fully serialized (no raw `date` objects) before calling duplicate detection or persistence.
