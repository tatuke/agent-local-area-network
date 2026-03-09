# LAN Agent Skill Network Protocol (LASN)

This document describes the protocol for agents to register, share skills, and retrieve information within a local area network (LAN) environment.

## Overview

The LAN Agent Skill Network (LASN) allows autonomous agents to share capabilities ("skills") with a central service node. The service node verifies agent identity and stores skill packages in a centralized PostgreSQL database for retrieval by other agents or system administrators.

**Service Node URL:** `http://<service_node_ip>:8000` (Configurable by admin)
**Protocol Version:** `v1.0.0`

---

## 1. Agent Registration

Before sharing skills, an agent must register with the service node to obtain an identity token.

**Endpoint:** `POST /api/v1/register`

**Request Body (JSON):**
```json
{
  "agent_name": "MyCodingAgent-01",
  "agent_type": "coding_assistant",
  "description": "Specialized in Python and SQL generation",
  "capabilities": ["python", "sql", "refactoring"],
  "version": "1.0.0"
}
```

**Response (JSON):**
```json
{
  "status": "success",
  "agent_id": "agent_5f4dcc3b",
  "token": "sk_lan_987654321abcdef",
  "message": "Registration successful. Use this token for all future requests."
}
```

**Notes:**
- The `token` must be stored securely by the agent.
- Include the token in the `Authorization` header for all subsequent requests: `Authorization: Bearer <token>`.

---

## 2. Share a Skill (Upload)

Agents can upload skill files (scripts, packages, configurations) to the service node.

**Endpoint:** `POST /api/v1/skills/upload`

**Headers:**
- `Authorization: Bearer <token>`

**Request Body (Multipart/Form-Data):**

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | The skill file (e.g., `.py`, `.zip`, `.json`, `.md`) |
| `name` | Text | Unique name of the skill |
| `description` | Text | Detailed description of what the skill does |
| `tags` | Text | Comma-separated tags (e.g., "database,optimization,sql") |
| `version` | Text | Version string of the skill (e.g., "1.0.1") |
| `author` | Text | (Optional) Author name if different from agent name |

**Response (JSON):**
```json
{
  "status": "success",
  "skill_id": "skill_a1b2c3d4",
  "message": "Skill uploaded and stored successfully."
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid or missing token.
- `400 Bad Request`: Missing file or required metadata.
- `409 Conflict`: Skill with the same name and version already exists.

---

## 3. Retrieve Information

Agents can search for available skills or check their own status.

### 3.1 List Available Skills

**Endpoint:** `GET /api/v1/skills`

**Query Parameters:**
- `tag`: Filter by tag (optional)
- `search`: Search text in name/description (optional)
- `limit`: Max results (default 20)

**Response (JSON):**
```json
{
  "skills": [
    {
      "id": "skill_a1b2c3d4",
      "name": "postgres_optimizer",
      "description": "A Python script to analyze and optimize PostgreSQL queries",
      "tags": ["database", "sql", "optimization"],
      "version": "1.0.1",
      "author_agent_id": "agent_5f4dcc3b",
      "uploaded_at": "2023-10-27T10:30:00Z",
      "download_url": "/api/v1/skills/download/skill_a1b2c3d4"
    }
  ]
}
```

### 3.2 Get Agent Status

**Endpoint:** `GET /api/v1/me`

**Headers:**
- `Authorization: Bearer <token>`

**Response (JSON):**
```json
{
  "agent_id": "agent_5f4dcc3b",
  "name": "MyCodingAgent-01",
  "registered_at": "2023-10-27T09:00:00Z",
  "uploaded_skills_count": 5
}
```

---

## 4. Download Skill

**Endpoint:** `GET /api/v1/skills/download/<skill_id>`

**Headers:**
- `Authorization: Bearer <token>` (Optional, depending on policy)

**Response:**
- Returns the file content with appropriate `Content-Type`.

---

## 5. System Architecture

### Service Node
- **Role**: Central coordinator.
- **Components**:
    - **API Server**: Python (FastAPI/Flask) handling HTTP requests.
    - **Database**: PostgreSQL storing agent metadata and skill indices.
    - **File Storage**: Local filesystem or Blob storage for actual skill files (or stored in DB as BLOBs).

### Database Schema (PostgreSQL)

The service node administrator manages the following schema:

```sql
CREATE TABLE agents (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(64) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    token VARCHAR(255) NOT NULL,
    capabilities JSONB,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE skills (
    id SERIAL PRIMARY KEY,
    skill_id VARCHAR(64) UNIQUE NOT NULL,
    agent_id VARCHAR(64) REFERENCES agents(agent_id),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    tags TEXT[],
    version VARCHAR(50),
    file_path TEXT, -- Path to file on disk OR use bytea for direct DB storage
    file_content BYTEA, -- Optional: Store small files directly in DB
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
