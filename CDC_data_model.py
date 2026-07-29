from sqlalchemy.orm import Mapped, mapped_column, sessionmaker, DeclarativeBase
from sqlalchemy import String, Float, create_engine, text
from typing import Optional
from dotenv import load_dotenv
import os 

load_dotenv()

engine = create_engine(os.getenv('DATABASE_URL_SCHEMA'))

try:
    with engine.connect() as con:
        result = con.execute(text("SELECT version();"))
        print("Connected to the Database")
except Exception as e:
    print('Failed to connect')
    print(e)
class Base(DeclarativeBase):
    pass
class Diabetes_Indicator(Base):
    __tablename__ = 'diabetes_ind'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[str] = mapped_column(String(4))
    indicator: Mapped[Optional[str]]
    unit: Mapped[Optional[str]]
    estimates: Mapped[Optional[float]]
    se_estimates: Mapped[Optional[float]]
    lower_limit: Mapped[Optional[float]]     
    upper_limit: Mapped[Optional[float]]
    population: Mapped[Optional[str]]      
    age: Mapped[Optional[str]]             
    race: Mapped[Optional[str]]            
    sex: Mapped[Optional[str]]
    eductaion: Mapped[Optional[str]]       
    
    def __repr__(self) -> str:
        return f"User(id={self.id!r},year={self.year!r},indicator={self.indicator!r},unit={self.unit!r},estimates={self.estimates!r},se_estimates={self.se_estimates!r},lower_limit={self.lower_limit!r},upper_limit={self.upper_limit!r},population={self.population!r},age={self.age!r},race={self.race!r},sex={self.sex!r},education={self.eductaion!r})"
    
class Stroke_Mortality(Base):
    __tablename__ = 'stroke_mortality'
    id: Mapped[int] = mapped_column(primary_key=True)
    year: Mapped[str] = mapped_column(String(4))
    state: Mapped[Optional[str]]
    location: Mapped[Optional[str]]
    geo_level: Mapped[Optional[str]]
    rate: Mapped[Optional[str]]
    sex: Mapped[Optional[str]]
    race: Mapped[Optional[str]]
    fips: Mapped[Optional[str]]
    
    def __repr__(self) -> str:
        return f"stroke_mortality(id={self.id!r},year={self.year!r},state={self.state!r},location={self.location!r},geo_level={self.geo_level!r},rate={self.rate!r},sex={self.sex!r},race={self.race!r},fips={self.fips!r})"
    

Base.metadata.create_all(engine)