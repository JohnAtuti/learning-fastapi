# BaseSettings = the class we inherit from; auto-reads .env.
# SettingsConfigDict = the config object controlling how env is loaded.

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DB_HOST:str
    DB_PORT:int = 3306
    DB_USER:str
    DB_PASSWORD:str
    DB_NAME:str
    APP_NAME:str = "FastAPI MySQL course"
    DEBUG:bool = False
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra= "ignore"
    )
    
    @property
    def database_url(self)->str:
        return(
            f"mysql+pymysql://" #dialect=mysql, driver=pymysql
            f"{self.DB_USER}:{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:{self.DB_PORT}"
            f"/{self.DB_NAME}"
            f"?charset=utf8mb4"
        )
# db_url format = mysql+pymysql://user:password@localhost:3306/db

settings = Settings()