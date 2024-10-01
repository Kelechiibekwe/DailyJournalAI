from flask_sqlalchemy import SQLAlchemy
import sqlalchemy.dialects.postgresql as pg

# Initialize SQLAlchemy
db = SQLAlchemy()

# Define the Prompts model
class Prompts(db.Model):
    prompt_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    prompt_text = db.Column(db.Text, nullable=False)
    embedding_vector = db.Column(pg.ARRAY(db.Float), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Define the Responses model
class Responses(db.Model):
    response_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    prompt_id = db.Column(db.Integer, nullable=False)
    response_text = db.Column(db.Text, nullable=False)
    embedding_vector = db.Column(pg.ARRAY(db.Float), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

# Define the User_Prompt model
class User_Prompt(db.Model):
    user_prompt_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    prompt_id = db.Column(db.Integer, nullable=False)
    message_id = db.Column(db.String(255), nullable=False, unique=True)
    sent_at = db.Column(db.DateTime, default=db.func.current_timestamp())
