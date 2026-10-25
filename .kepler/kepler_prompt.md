# Kepler Remediation Task: Automated Verification & Breaking-Change Refactoring

## Background
Temporal has executed Phase 1 and is currently in state `PAUSED (Awaiting Review)`.
Gemma 4 has analyzed `requirements.txt` and generated:
1. `upgraded_requirements.txt` (Upgrades `pydantic` to 2.x, `requests` to 2.31+, `fastapi` to 0.111+)
2. `gemma_advisory.json` (Flagged breaking change: Pydantic v1 `class Config` & `@validator` deprecated)
3. `.kepler/kepler_handoff.json` (Task specifications)

---

## Kepler Instructions

### 1. Verification Dry-Run
Run the test suite to observe breaking changes:
```bash
pytest service/tests/test_models.py
```
Observe the failure/deprecation traces caused by Pydantic v1 syntax under upgraded dependencies.

### 2. Automated Refactor in `service/models.py`
Refactor `service/models.py` to Pydantic v2 syntax:
- Import `ConfigDict` and `field_validator` from `pydantic`:
  ```python
  from pydantic import BaseModel, ConfigDict, field_validator
  ```
- Replace `@validator("username")` with:
  ```python
  @field_validator("username")
  @classmethod
  def validate_username(cls, v: str) -> str:
      if len(v) < 3:
          raise ValueError("Username must be at least 3 characters")
      return v.lower()
  ```
- Replace `class Config:` with:
  ```python
  model_config = ConfigDict(
      populate_by_name=True,
      json_schema_extra={
          "example": {
              "user_id": 101,
              "username": "sre_admin",
              "email": "sre@cloudnativepune.org",
              "bio": "DevOps & SRE Engineer",
              "is_active": True,
          }
      }
  )
  ```

### 3. Re-Verify & Check Green
Run:
```bash
pytest service/tests/test_models.py
```
Ensure all tests pass.

### 4. Emit Verification Signal
Run the signal script to notify Temporal that Kepler verification succeeded:
```bash
python engine/signal_kepler.py
```
