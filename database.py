from sqlalchemy import create_engine, Column, Integer, String, LargeBinary, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
import os
import pickle

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///databot.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    datasets = relationship("Dataset", back_populates="owner")
    chat_histories = relationship("ChatHistory", back_populates="user")

class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    data = Column(LargeBinary, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="datasets")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"))
    result = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChatHistory(Base):
    __tablename__ = "chat_histories"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(Text)
    response = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user = relationship("User", back_populates="chat_histories")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_user(username, create=False):
    session = SessionLocal()
    user = session.query(User).filter(User.username == username).first()
    if not user and create:
        user = User(username=username)
        session.add(user)
        session.commit()
        session.refresh(user)
    session.close()
    return user

def save_dataset(user_id, name, df):
    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        session.close()
        return False
    data_bytes = pickle.dumps(df)
    dataset = session.query(Dataset).filter(Dataset.user_id == user_id, Dataset.name == name).first()
    if dataset:
        dataset.data = data_bytes
    else:
        dataset = Dataset(name=name, data=data_bytes, owner=user)
        session.add(dataset)
    session.commit()
    session.close()
    return True

def load_dataset(user_id, dataset_name=None, list_only=False):
    session = SessionLocal()
    if list_only:
        datasets = session.query(Dataset).filter(Dataset.user_id == user_id).all()
        session.close()
        return [d.name for d in datasets]
    if dataset_name:
        dataset = session.query(Dataset).filter(Dataset.user_id == user_id, Dataset.name == dataset_name).first()
        if dataset:
            df = pickle.loads(dataset.data)
            session.close()
            return df
    session.close()
    return None

def save_chat_history(user_id, message, response):
    session = SessionLocal()
    chat = ChatHistory(user_id=user_id, message=message, response=response)
    session.add(chat)
    session.commit()
    session.close()

def get_chat_history(user_id, limit=50):
    session = SessionLocal()
    chats = session.query(ChatHistory).filter(ChatHistory.user_id == user_id).order_by(ChatHistory.timestamp.desc()).limit(limit).all()
    session.close()
    return chats
