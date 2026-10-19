from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="AI API Testing Agent Demo API", version="1.0.0")

USERS = {
    1: {"id": 1, "name": "Arun"},
    2: {"id": 2, "name": "Priya"},
}

class UserCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

class UserUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=80)

@app.get("/users")
def get_users():
    return list(USERS.values())

@app.get("/users/{user_id}")
def get_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    return USERS[user_id]

@app.post("/users", status_code=201)
def create_user(user: UserCreate):
    # Reuse the first free ID from 3 upward so the demo remains repeatable.
    user_id = 3
    while user_id in USERS:
        user_id += 1
    USERS[user_id] = {"id": user_id, "name": user.name}
    return USERS[user_id]

@app.put("/users/{user_id}")
def update_user(user_id: int, user: UserUpdate):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    USERS[user_id] = {"id": user_id, "name": user.name}
    return USERS[user_id]

@app.delete("/users/{user_id}", status_code=204)
def delete_user(user_id: int):
    if user_id not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    del USERS[user_id]
    return Response(status_code=204)
