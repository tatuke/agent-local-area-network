from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Header, status, Response
from fastapi.responses import JSONResponse, Response as FastAPIResponse
from typing import List, Optional
import uuid
import secrets
import json
from datetime import datetime
from pydantic import BaseModel

from database import db, get_db_pool
from config import settings

app = FastAPI(title="LAN Agent Skill Network Service Node", version="1.0.0")

# --- Models ---

class AgentRegisterRequest(BaseModel):
    agent_name: str
    agent_type: str
    description: Optional[str] = None
    capabilities: List[str] = []
    version: str = "1.0.0"

class AgentRegisterResponse(BaseModel):
    status: str
    agent_id: str
    token: str
    message: str

class SkillInfo(BaseModel):
    id: str
    name: str
    description: Optional[str]
    tags: List[str]
    version: str
    author_agent_id: str
    uploaded_at: datetime
    filename: str

class SkillListResponse(BaseModel):
    skills: List[SkillInfo]

class AgentInfo(BaseModel):
    agent_id: str
    name: str
    registered_at: datetime
    uploaded_skills_count: int

# --- Dependencies ---

async def get_current_agent(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing Authorization header",
        )
    
    token = authorization.split(" ")[1]
    pool = await get_db_pool()
    
    async with pool.acquire() as conn:
        agent = await conn.fetchrow("SELECT * FROM agents WHERE token = $1", token)
        
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
        
    return agent

# --- Events ---

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# --- Endpoints ---

@app.post("/api/v1/register", response_model=AgentRegisterResponse)
async def register_agent(payload: AgentRegisterRequest):
    agent_id = f"agent_{uuid.uuid4().hex[:8]}"
    token = f"sk_lan_{secrets.token_hex(16)}"
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        try:
            await conn.execute(
                """
                INSERT INTO agents (agent_id, name, token, description, capabilities)
                VALUES ($1, $2, $3, $4, $5)
                """,
                agent_id,
                payload.agent_name,
                token,
                payload.description,
                json.dumps(payload.capabilities)
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
            
    return AgentRegisterResponse(
        status="success",
        agent_id=agent_id,
        token=token,
        message="Registration successful. Use this token for all future requests."
    )

@app.post("/api/v1/skills/upload")
async def upload_skill(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(None),
    tags: str = Form(""), # Comma-separated
    version: str = Form("1.0.0"),
    agent: dict = Depends(get_current_agent)
):
    skill_id = f"skill_{uuid.uuid4().hex[:8]}"
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    file_content = await file.read()
    
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        # Check if skill with same name/version exists
        existing = await conn.fetchrow(
            "SELECT id FROM skills WHERE name = $1 AND version = $2",
            name, version
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Skill '{name}' version '{version}' already exists."
            )
            
        await conn.execute(
            """
            INSERT INTO skills (skill_id, agent_id, name, description, tags, version, filename, file_content)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            skill_id,
            agent['agent_id'],
            name,
            description,
            tag_list,
            version,
            file.filename,
            file_content
        )
        
    return {
        "status": "success",
        "skill_id": skill_id,
        "message": "Skill uploaded and stored successfully."
    }

@app.get("/api/v1/skills", response_model=SkillListResponse)
async def list_skills(
    tag: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 20
):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        query = "SELECT * FROM skills"
        params = []
        conditions = []
        
        if tag:
            conditions.append(f"$1 = ANY(tags)")
            params.append(tag)
            
        if search:
            idx = len(params) + 1
            conditions.append(f"(name ILIKE ${idx} OR description ILIKE ${idx})")
            params.append(f"%{search}%")
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += f" ORDER BY uploaded_at DESC LIMIT ${len(params) + 1}"
        params.append(limit)
        
        rows = await conn.fetch(query, *params)
        
    skills = []
    for row in rows:
        skills.append(SkillInfo(
            id=row['skill_id'],
            name=row['name'],
            description=row['description'],
            tags=row['tags'] if row['tags'] else [],
            version=row['version'],
            author_agent_id=row['agent_id'],
            uploaded_at=row['uploaded_at'],
            filename=row['filename'] or "unknown"
        ))
        
    return SkillListResponse(skills=skills)

@app.get("/api/v1/skills/download/{skill_id}")
async def download_skill(skill_id: str):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT filename, file_content FROM skills WHERE skill_id = $1", skill_id)
        
    if not row:
        raise HTTPException(status_code=404, detail="Skill not found")
        
    return FastAPIResponse(
        content=row['file_content'],
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename={row['filename']}"}
    )

@app.get("/api/v1/me", response_model=AgentInfo)
async def get_my_info(agent: dict = Depends(get_current_agent)):
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        count = await conn.fetchval("SELECT COUNT(*) FROM skills WHERE agent_id = $1", agent['agent_id'])
        
    return AgentInfo(
        agent_id=agent['agent_id'],
        name=agent['name'],
        registered_at=agent['registered_at'],
        uploaded_skills_count=count
    )

if __name__ == "__main__":
    import uvicorn
    import argparse
    import sys
    import os
    import subprocess

    parser = argparse.ArgumentParser(description="LAN Agent Service Node")
    parser.add_argument("--daemon", action="store_true", help="Run the service in background (daemon mode)")
    args = parser.parse_args()

    if args.daemon:
        # Remove --daemon from arguments to prevent infinite loop in subprocess
        # We need to construct the command correctly: [python_executable, script_path, args...]
        executable = sys.executable
        script_path = os.path.abspath(sys.argv[0])
        # Filter out --daemon
        remaining_args = [arg for arg in sys.argv[1:] if arg != "--daemon"]
        
        cmd = [executable, script_path] + remaining_args
        
        # Log file for background process
        log_file = "service.log"
        
        try:
            with open(log_file, "a") as log:
                kwargs = {}
                if os.name == 'nt':
                    # Windows: Use CREATE_NO_WINDOW flag (0x08000000)
                    kwargs['creationflags'] = 0x08000000
                    kwargs['close_fds'] = True
                else:
                    # Unix/Linux: Start new session
                    kwargs['start_new_session'] = True
                
                # Launch subprocess
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=log,
                    **kwargs
                )
                
                print(f"Service started in background with PID: {process.pid}")
                print(f"Logs are being written to: {os.path.abspath(log_file)}")
                sys.exit(0)
        except Exception as e:
            print(f"Failed to start daemon: {e}")
            sys.exit(1)

    # Normal foreground execution
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=True)
