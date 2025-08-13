import os
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_EXPIRES_DAYS = int(os.getenv("JWT_EXPIRES_DAYS", "7"))
FRONTEND_ORIGINS = [origin.strip() for origin in os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")]
PORT = int(os.getenv("PORT", 5000))
