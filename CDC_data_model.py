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
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    api_id: Mapped[str] = mapped_column(unique=True, nullable=False)   
    year: Mapped[str] = mapped_column(String(4), nullable= True)
    indicator: Mapped[Optional[str]] = mapped_column(nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(nullable=True)
    estimate: Mapped[Optional[float]] = mapped_column(nullable=True)
    se_estimate: Mapped[Optional[float]] = mapped_column(nullable=True)
    lower_limit: Mapped[Optional[float]] = mapped_column(nullable=True)    
    upper_limit: Mapped[Optional[float]] = mapped_column(nullable=True)
    population: Mapped[Optional[str]] = mapped_column(nullable=True)     
    age: Mapped[Optional[str]] = mapped_column(nullable=True)            
    race: Mapped[Optional[str]]  = mapped_column(nullable=True)           
    sex: Mapped[Optional[str]] = mapped_column(nullable=True)
    education: Mapped[Optional[str]] = mapped_column(nullable=True)       
    other_info: Mapped[Optional[str]] = mapped_column(nullable=True)
    

    def __repr__(self) -> str:
        return f"User(id={self.id!r},year={self.year!r},indicator={self.indicator!r},unit={self.unit!r},estimates={self.estimates!r},se_estimates={self.se_estimates!r},lower_limit={self.lower_limit!r},upper_limit={self.upper_limit!r},population={self.population!r},age={self.age!r},race={self.race!r},sex={self.sex!r},education={self.education!r})"
    
class Stroke_Mortality(Base):
    __tablename__ = 'stroke_mortality'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    api_id: Mapped[str] = mapped_column(unique=True, nullable=False)   
    year: Mapped[str] = mapped_column(String(4), nullable=True)
    icd_class: Mapped[Optional[str]] = mapped_column(nullable=True)
    state: Mapped[Optional[str]]  = mapped_column(nullable=True)
    location: Mapped[Optional[str]] = mapped_column(nullable=True)
    geo_level: Mapped[Optional[str]] = mapped_column(nullable=True)
    value: Mapped[Optional[float]] = mapped_column(nullable=True)
    rate: Mapped[Optional[str]] = mapped_column(nullable=True)
    sex: Mapped[Optional[str]] = mapped_column(nullable=True)
    race: Mapped[Optional[str]] = mapped_column(nullable=True)
    fips: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        return f"stroke_mortality(id={self.id!r},year={self.year!r},state={self.state!r},location={self.location!r},geo_level={self.geo_level!r},rate={self.rate!r},sex={self.sex!r},race={self.race!r},fips={self.fips!r})"
    

Base.metadata.create_all(engine)
