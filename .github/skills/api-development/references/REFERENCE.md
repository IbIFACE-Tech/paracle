# API Development Reference Guide

This document provides extended patterns and best practices for API development with FastAPI.

## Table of Contents

- [Advanced Request Handling](#advanced-request-handling)
- [Response Models](#response-models)
- [Pagination Patterns](#pagination-patterns)
- [Filtering and Sorting](#filtering-and-sorting)
- [Background Tasks](#background-tasks)
- [WebSocket Support](#websocket-support)

## Advanced Request Handling

### File Uploads

```python
from fastapi import UploadFile, File

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    contents = await file.read()
    # Process file
    return {"filename": file.filename, "size": len(contents)}
```

### Form Data

```python
from fastapi import Form

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    # Authenticate user
    return {"access_token": token}
```

### Request Body with Multiple Models

```python
from pydantic import BaseModel
from typing import Union

class ImageData(BaseModel):
    url: str
    alt: str

class TextData(BaseModel):
    content: str
    format: str

@app.post("/content")
async def create_content(data: Union[ImageData, TextData]):
    # Handle either type
    return data
```

## Response Models

### Excluding Unset Fields

```python
@app.get("/agents/{id}", response_model=AgentResponse, response_model_exclude_unset=True)
async def get_agent(id: str):
    # Only return fields that are set
    return agent
```

### Multiple Response Models

```python
from fastapi.responses import JSONResponse

@app.get("/data")
async def get_data(format: str = "json"):
    data = fetch_data()

    if format == "csv":
        return Response(content=to_csv(data), media_type="text/csv")

    return JSONResponse(content=data)
```

## Pagination Patterns

### Offset-Based Pagination

```python
from fastapi import Query

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    offset: int
    limit: int

@app.get("/items", response_model=PaginatedResponse)
async def list_items(
    offset: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
):
    items = fetch_items(offset, limit)
    total = count_items()

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
    )
```

### Cursor-Based Pagination

```python
@app.get("/items")
async def list_items(cursor: Optional[str] = None, limit: int = 10):
    items, next_cursor = fetch_items_after(cursor, limit)

    return {
        "items": items,
        "next_cursor": next_cursor,
        "has_more": next_cursor is not None,
    }
```

## Filtering and Sorting

### Query Parameters

```python
from enum import Enum

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"

@app.get("/agents")
async def list_agents(
    status: Optional[str] = None,
    model: Optional[str] = None,
    sort_by: str = "created_at",
    order: SortOrder = SortOrder.DESC,
):
    filters = {}
    if status:
        filters["status"] = status
    if model:
        filters["model"] = model

    agents = fetch_agents(filters, sort_by, order)
    return agents
```

### Complex Filtering

```python
from fastapi import Query

@app.get("/search")
async def search(
    q: str = Query(..., min_length=1),
    tags: List[str] = Query([]),
    min_score: float = Query(0.0, ge=0.0, le=1.0),
):
    results = search_items(
        query=q,
        tags=tags,
        min_score=min_score,
    )
    return results
```

## Background Tasks

### Simple Background Task

```python
from fastapi import BackgroundTasks

def send_notification(email: str, message: str):
    # Send email (time-consuming)
    send_email(email, message)

@app.post("/process")
async def process_data(
    data: DataInput,
    background_tasks: BackgroundTasks,
):
    # Process immediately
    result = process(data)

    # Send notification in background
    background_tasks.add_task(
        send_notification,
        data.email,
        "Processing complete",
    )

    return result
```

### Task Queue Integration

```python
from celery import Celery

celery = Celery("tasks", broker="redis://localhost:6379")

@celery.task
def process_heavy_task(data_id: str):
    # Long-running task
    pass

@app.post("/heavy-task")
async def create_task(data: DataInput):
    # Queue task
    task = process_heavy_task.delay(data.id)

    return {"task_id": task.id, "status": "queued"}
```

## WebSocket Support

### Basic WebSocket

```python
from fastapi import WebSocket

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except:
        pass
```

### WebSocket with Authentication

```python
@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user = await authenticate_token(token)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    # Handle messages
```

## API Versioning

### URL Path Versioning

```python
from fastapi import APIRouter

v1_router = APIRouter(prefix="/v1")
v2_router = APIRouter(prefix="/v2")

@v1_router.get("/agents")
async def list_agents_v1():
    # Version 1 implementation
    pass

@v2_router.get("/agents")
async def list_agents_v2():
    # Version 2 implementation
    pass

app.include_router(v1_router)
app.include_router(v2_router)
```

### Header-Based Versioning

```python
from fastapi import Header

@app.get("/agents")
async def list_agents(api_version: str = Header("1.0")):
    if api_version == "2.0":
        return list_agents_v2()
    return list_agents_v1()
```

## See Also

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- `SKILL.md` for quick reference patterns
