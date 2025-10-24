from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    # Base de datos
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'rca_database')
    
    # Servidor
    SERVER_HOST = os.getenv('SERVER_HOST', '0.0.0.0')
    SERVER_PORT = int(os.getenv('SERVER_PORT', 8000))
    
    # Rutas
    ARCHIVOS_PATH = os.getenv('ARCHIVOS_PATH', '../archivos')
    RESPALDOS_PATH = os.getenv('RESPALDOS_PATH', '../respaldos')
    
    @property
    def database_url(self):
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

config = Config()