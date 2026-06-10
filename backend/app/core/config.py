import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL").strip() # type: ignore
SUPABASE_PUBLISHABLE_KEY = os.getenv("SUPABASE_PUBLISHABLE_KEY").strip() # type: ignore
DATABASE_URL = os.getenv("DATABASE_URL").strip() # type: ignore

# Just allows to be called easier no need to find path all the time.