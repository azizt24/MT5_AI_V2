import os
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()

class Credentials:
    @staticmethod
    def mt5() -> Dict[str, Any]:
        """Load and validate MT5 credentials with enhanced checks"""
        config = {
            "server": os.getenv("SERVER"),
            "login": os.getenv("LOGIN"),
            "password": os.getenv("PASSWORD"),
        }
        
        missing = [k.upper() for k, v in config.items() if not v]
        if missing:
            raise ValueError(f"Missing MT5 credentials: {missing}")
            
        try:
            config["login"] = int(config["login"])
        except ValueError:
            raise ValueError("MT5 login must be numeric")
            
        return config

    @staticmethod
    def openai() -> str:
        """Validate OpenAI credentials"""
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not found")
        return key