import os
from dotenv import load_dotenv

from fastapi import FastAPI,Depends,Query
from typing import Annotated
app = FastAPI()
from sqlmodel import Field, Session, SQLModel, create_engine, select
load_dotenv()
db_user=os.getenv("USER_DB")
db_password=os.getenv("PASSWORD_DB")
db_host=os.getenv("HOST_DB")
db_port=os.getenv("PORT_DB")
db_name=os.getenv("NAME_DB")    
print(db_user,db_password,db_host,db_port,db_name)
url_connection=f'mysql+pymysql://{db_user}:{db_password}@{db_host}:3306/{db_name}'
engine=create_engine(url_connection)
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
def get_session():
    with Session(engine) as session:
        yield session

session_dep=Annotated[Session, Depends(get_session)]
#definiendo modelos

class HeroBase(SQLModel):
    name: str
    
    age: int | None = Field(default=None, index=True)
class Hero(HeroBase , table=True):
    id: int = Field(default=None, primary_key=True)
    secret_name: str
class HeroPublic(HeroBase):
    id: int
class HeroCreate(HeroBase):
    secret_name: str
class HeroUpdate(HeroBase):
    name: str | None 
    age: int | None
    secret_name: str | None= None
@app.get("/")
def read_root():
    return {"Hello": "World"}
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.post("/heroes/", response_model=HeroPublic)
def create_hero(hero: HeroCreate, session: session_dep):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero
@app.get("/heroes/", response_model=list[HeroPublic])
def read_heroes(session: session_dep,
                offset: int = 0, limit: Annotated[int, Query(le=100)] = 100):

    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes
@app.get("/heroes/{hero_id}", response_model=HeroPublic)
def read_hero(hero_id: int, session: session_dep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
@app.patch("/heroes/{hero_id}", response_model=HeroPublic)
def update_hero(hero_id: int, hero_update: HeroUpdate, session: session_dep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    hero_data = hero_update.model_dump(exclude_unset=True)
    for key, value in hero_data.items():
        setattr(hero, key, value)
    
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero 
@app.delete("/heroes/{hero_id}")
def delete_hero(hero_id: int, session: session_dep):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    
    session.delete(hero)
    session.commit()
    return {"ok": True}