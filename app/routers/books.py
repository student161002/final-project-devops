from fastapi import APIRouter, Depends, Request, Form, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pathlib import Path

from app import models, schemas
from app.database import SessionLocal

router = APIRouter(prefix="/books")
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/list")
def list_books_html(request: Request, db: Session = Depends(get_db)):
    books = db.query(models.Book).all()
    return templates.TemplateResponse("index.html", {"request": request, "books": books})

@router.get("/", response_model=list[schemas.Book])
def read_books_json(db: Session = Depends(get_db)):
    return db.query(models.Book).all()


@router.post("/", response_model=schemas.Book)
def create_book(book: schemas.BookCreate, db: Session = Depends(get_db)):
    obj = models.Book(
        title=book.title,
        author=book.author,
        description=book.description,
        year=book.year
    )
    
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.get("/{book_id}/edit")
def edit_book_form(request: Request, book_id: int, db: Session = Depends(get_db)):
    book = db.query(models.Book).filter(models.Book.id == book_id).first()
    
    return templates.TemplateResponse("edit_book.html", {"request": request, "book": book})


@router.post("/{book_id}/edit")
def update_book(
    book_id: int,
    title: str = Form(...),   
    author: str = Form(...),
    description: str = Form(...),
    year: int = Form(...),
    db: Session = Depends(get_db)
):
    book_query = db.query(models.Book).filter(models.Book.id == book_id)
    book = book_query.first()

    book.title = title
    book.author = author
    book.description = description
    book.year = year

    db.commit()
    
    return RedirectResponse(url="/books/list", status_code=status.HTTP_303_SEE_OTHER)
