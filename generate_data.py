
import json
import random
import hashlib
from datetime import datetime, timedelta

lines = ["Sarmiento", "Mitre", "Roca", "San Martín", "Belgrano Sur"]
statuses = ["APROBADO", "RECHAZADO"]
motivos = ["-", "Tono incorrecto", "Falta horario", "Error de ortografía", "Mensaje confuso"]

data = []
base_time = datetime(2026, 1, 27, 8, 0, 0)

for i in range(170):
    timestamp = base_time + timedelta(minutes=random.randint(0, 480))
    line = random.choice(lines)
    status = random.choice(statuses)
    motivo = "-" if status == "APROBADO" else random.choice(motivos[1:])
    
    data.append({
        "id": f"MSG-{1000+i}",
        "timestamp": timestamp.strftime("%Y-%m-%d %H:%M"),
        "linea": line,
        "estado": status,
        "motivo": motivo,
        "auditor": "HUMANO_SYS_01"
    })

file_path = "auditoria/releases/v1.0/data/dataset_170_casos.json"
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

# Compute SHA256 of the JSON
sha256_hash = hashlib.sha256()
with open(file_path, "rb") as f:
    for byte_block in iter(lambda: f.read(4096), b""):
        sha256_hash.update(byte_block)

sha_file = "auditoria/releases/v1.0/data/SHA256SUMS.txt"
with open(sha_file, "w", encoding="utf-8") as f:
    f.write(f"{sha256_hash.hexdigest()}  dataset_170_casos.json\n")

print(f"Dataset created at {file_path}")
print(f"SHA256 created at {sha_file}")
