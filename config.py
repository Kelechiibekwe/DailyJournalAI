import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Define the base directory where the app will be located
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Email and API credentials
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
