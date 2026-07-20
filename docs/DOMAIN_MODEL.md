# Shield EPC Domain Model

## 1. Purpose

Canonical domain model for Shield EPC. This document distinguishes between implemented entities (verified from source code) and architecture-specified entities that are not yet implemented.

## 2. Evidence Baseline

Repository: Shield-EPC-project-V_0

Verified implementation sources:

- backend/app/db/models.py
- backend/app/hazards/library.py
- backend/app/standards/models.py
- backend/app/envelope/schema.py
- docs/ShieldEPC_Architecture_Spec_v1.md

## 3. Verified Domain Entities

### Tenant

Attributes:
- tenant_id
- name
- status
- created_at

### Project

Attributes:
- project_id
- tenant_id
- name
- created_at

Relationship:
- One Tenant owns many Projects.

### Hazard

Read-only hazard catalogue.

### StandardClause

References hazard IDs from the Hazard catalogue.

### ResponseEnvelope

Mandatory API response envelope.
