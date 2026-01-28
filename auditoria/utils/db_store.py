
import json
import os
import shutil
import time
import datetime
from filelock import FileLock

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = os.path.abspath(db_path)
        self.lock_path = f"{self.db_path}.lock"
        self.lock = FileLock(self.lock_path, timeout=10) # 10s wait before crash
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def _create_backup(self):
        """Rotación simple de backups (ultimo 5 cambios)"""
        if not os.path.exists(self.db_path): return
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(os.path.dirname(self.db_path), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f"auditoria_logs_{timestamp}.json")
        shutil.copy2(self.db_path, backup_file)
        
        # Rotación (limpieza) opcional future work
        # print(f"Backup creado: {backup_file}")

    def read(self):
        """Lectura con lock compartido (en este caso usamos lock exclusivo por simplicidad P0)"""
        with self.lock:
            if not os.path.exists(self.db_path): return []
            try:
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print("❌ ERROR: DB corrupta durante lectura.")
                return []

    def atomic_write(self, data):
        """Escritura atómica real: write tmp -> fsync -> rename"""
        # IMPORTANTE: El lock debe obtenerse ANTES de leer y mantenerse hasta DESPUES de escribir
        # Si esta funcion se usa sola, asume que 'data' ya tiene lo que queres.
        # Pero para Read-Modify-Write, el caller debe manejar el lock context.
        pass # Helper interno

    def update_record(self, record_id, update_func):
        """
        Transacción Atómica: Read -> Modify -> Write
        record_id: ID del item a buscar
        update_func: función lambda que recibe el item y lo modifica (in-place)
        """
        start = time.time()
        try:
            with self.lock:
                # 1. Backup Pre-Write
                self._create_backup()

                # 2. Read
                with open(self.db_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 3. Modify
                modified = False
                for item in data:
                    if str(item.get('id', '')) == str(record_id):
                        update_func(item)
                        modified = True
                        break
                
                if not modified:
                    print(f"⚠️ Warning: Record {record_id} not found for update.")
                    return False

                # 4. Atomic Write (Write tmp -> Rename)
                tmp_path = f"{self.db_path}.tmp"
                with open(tmp_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                    f.flush()
                    os.fsync(f.fileno()) # Force write to disk
                
                os.replace(tmp_path, self.db_path)
                
                duration = (time.time() - start) * 1000
                print(f"✅ TX Success: ID {record_id} updated via Lock ({duration:.2f}ms)")
                return True
                
        except Exception as e:
            print(f"❌ TX FAILED: {e}")
            return False

# Singleton Factory
def get_db(path):
    return DatabaseManager(path)
