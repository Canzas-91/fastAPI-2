from fastapi import FastAPI, Response, Cookie, Request, HTTPException
from pydantic import BaseModel, validator
from itsdangerous import TimestampSigner, BadSignature
from datetime import datetime
import uuid, time, re

app = FastAPI()

SECRET_KEY = "super-secret-key"
signer = TimestampSigner(SECRET_KEY)
SESSION_LIFETIME = 300
RENEW_THRESHOLD = 180 
fake_users = {"user123456": "password123456"}
user_ids = {"user123456": str(uuid.uuid4())}

class LoginData(BaseModel):
    username: str
    password: str

def make_token(user_id: str) -> str:
    timestamp = str(int(time.time()))
    payload = f"{user_id}.{timestamp}"
    return signer.sign(payload).decode()

def parse_token(token: str):
    try:
        unsigned = signer.unsign(token).decode()
        user_id, timestamp = unsigned.rsplit(".", 1)
        return user_id, int(timestamp)
    except (BadSignature, ValueError):
        return None, None

@app.post("/login")
def login(data: LoginData, response: Response):
    if fake_users.get(data.username) != data.password:
        response.status_code = 401
        return {"message": "Unauthorized"}
    user_id = user_ids[data.username]
    token = make_token(user_id)
    response.set_cookie("session_token", token, httponly=True, max_age=SESSION_LIFETIME)
    return {"message": "Logged in"}

@app.get("/user")
def get_user(response: Response, session_token: str = Cookie(default=None)):
    if not session_token:
        response.status_code = 401
        return {"message": "Unauthorized"}
    user_id, ts = parse_token(session_token)
    if user_id is None:
        response.status_code = 401
        return {"message": "Unauthorized"}
    return {"user_id": user_id, "username": "user123456"}

@app.get("/profile")
def profile(response: Response, session_token: str = Cookie(default=None)):
    if not session_token:
        response.status_code = 401
        return {"message": "Unauthorized"}

    user_id, ts = parse_token(session_token)

    if user_id is None:
        response.status_code = 401
        return {"message": "Invalid session"}

    elapsed = int(time.time()) - ts

    if elapsed >= SESSION_LIFETIME:
        response.status_code = 401
        return {"message": "Session expired"}

    if RENEW_THRESHOLD <= elapsed < SESSION_LIFETIME:
        new_token = make_token(user_id)
        response.set_cookie("session_token", new_token, httponly=True, max_age=SESSION_LIFETIME)

    return {"user_id": user_id, "message": "Profile data"}


@app.get("/headers")
def get_headers(request: Request):
    user_agent = request.headers.get("User-Agent")
    accept_language = request.headers.get("Accept-Language")
    if not user_agent:
        raise HTTPException(status_code=400, detail="Missing User-Agent header")
    if not accept_language:
        raise HTTPException(status_code=400, detail="Missing Accept-Language header")
    return {
        "User-Agent": user_agent,
        "Accept-Language": accept_language
    }
class CommonHeaders(BaseModel):
    user_agent: str
    accept_language: str

    @validator("accept_language")
    def validate_accept_language(cls, v):
        pattern = r'^[a-zA-Z\-]{2,10}(,[a-zA-Z\-]{2,10}(;q=\d\.\d)?)*$'
        if not re.match(pattern, v):
            raise ValueError("Invalid Accept-Language format")
        return v

def extract_common_headers(request: Request) -> CommonHeaders:
    ua = request.headers.get("User-Agent", "")
    al = request.headers.get("Accept-Language", "")
    if not ua:
        raise HTTPException(status_code=400, detail="Missing User-Agent header")
    if not al:
        raise HTTPException(status_code=400, detail="Missing Accept-Language header")
    return CommonHeaders(user_agent=ua, accept_language=al)

@app.get("/headers")
def headers_route(request: Request):
    h = extract_common_headers(request)
    return {"User-Agent": h.user_agent, "Accept-Language": h.accept_language}

@app.get("/info")
def info_route(request: Request, response: Response):
    h = extract_common_headers(request)
    response.headers["X-Server-Time"] = datetime.now().isoformat(timespec="seconds")
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": h.user_agent,
            "Accept-Language": h.accept_language
        }
    }
