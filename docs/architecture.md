
### Investigator Sign-off Model (Phase 4B)

The investigator sign-off workflow uses conditional validation to preserve audit integrity.

- `status="pending"`
  - `investigator_id` is optional (`None`)
  - `signed_at` must be `None`
- `status="signed"` or `status="rejected"`
  - `investigator_id` is required
  - `signed_at` is required and must be timezone-aware

This design intentionally avoids placeholder identifiers (e.g. `"pending"` or `"system"`). An investigator ID is recorded only after a real investigator completes the sign-off process.
