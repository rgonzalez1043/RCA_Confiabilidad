"""
Utilidad para respaldos automáticos
"""
import os
import shutil
import subprocess
from datetime import datetime
from config import config

def backup_database():
    """
    Realiza respaldo de la base de datos MySQL/MariaDB
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(config.RESPALDOS_PATH, f'db_backup_{timestamp}.sql')
    
    # Asegurar que existe la carpeta de respaldos
    os.makedirs(config.RESPALDOS_PATH, exist_ok=True)
    
    # Comando mysqldump (ajustar ruta según instalación XAMPP)
    mysqldump_path = r'C:\xampp\mysql\bin\mysqldump.exe'
    
    command = [
        mysqldump_path,
        '-u', config.DB_USER,
        f'-p{config.DB_PASSWORD}',
        config.DB_NAME,
        '--result-file', backup_file
    ]
    
    try:
        subprocess.run(command, check=True, capture_output=True)
        print(f"? Backup de base de datos creado: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print(f"? Error al crear backup: {e}")
        return None

def backup_archivos():
    """
    Realiza respaldo de la carpeta de archivos
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_folder = os.path.join(config.RESPALDOS_PATH, f'archivos_{timestamp}')
    
    try:
        shutil.copytree(config.ARCHIVOS_PATH, backup_folder)
        print(f"? Backup de archivos creado: {backup_folder}")
        return backup_folder
    except Exception as e:
        print(f"? Error al respaldar archivos: {e}")
        return None

def backup_completo():
    """
    Realiza respaldo completo (base de datos + archivos)
    """
    print(f"\n{'='*50}")
    print(f"?? Iniciando respaldo completo...")
    print(f"{'='*50}\n")
    
    db_backup = backup_database()
    archivos_backup = backup_archivos()
    
    print(f"\n{'='*50}")
    if db_backup and archivos_backup:
        print(f"? Respaldo completo exitoso")
    else:
        print(f"?? Respaldo completado con errores")
    print(f"{'='*50}\n")
    
    return db_backup, archivos_backup

def limpiar_backups_antiguos(dias_mantener=30):
    """
    Elimina respaldos más antiguos que X días
    """
    # Implementar si lo necesitas
    pass

if __name__ == "__main__":
    backup_completo()