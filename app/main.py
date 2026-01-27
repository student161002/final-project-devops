import os
from fastapi import FastAPI, Request, Depends, HTTPException, Form
from pathlib import Path
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from routers import books
from database import Base, engine, get_db
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from auth import authenticate_user, create_access_token
from datetime import timedelta

Base.metadata.create_all(bind=engine)

app = FastAPI(title="LibraryLite")

Instrumentator().instrument(app).expose(app)

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.include_router(books.router)


@app.on_event("startup")
async def startup_event():
    from app.init_db import init_db
    init_db()


@app.get("/")
def home(request: Request):
    return RedirectResponse(url="/books/list")

@app.post("/token")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPExeption(status_code=400, detail="Niepoprawny login lub hasło")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error":"Błędny login lub hasło"})
    token = create_access_token(data={"sub": user.username}, expires_delta=timedelta(minutes=60))
    response = RedirectResponse("/books/list", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {token}", httponly=True)
    return response

@app.get("/logout")
def logout():
    resp = RedirectResponse("/books/list", status_code=303)
    resp.delete_cookie("access_token")
    return resp

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
