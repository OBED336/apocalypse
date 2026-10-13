import os

BASE = os.path.dirname(os.path.abspath(__file__))
PACK = os.path.join(BASE, "kenney_animated-characters-survivors")

print("=" * 60)
print("EXPLORANDO PACK DE KENNEY")
print("=" * 60)

for root, dirs, files in os.walk(PACK):
    nivel = root.replace(PACK, "").count(os.sep)
    indent = "  " * nivel
    print(f"{indent}📁 {os.path.basename(root)}/")
    for f in files[:10]:  # Solo primeros 10 archivos
        tamaño = os.path.getsize(os.path.join(root, f))
        print(f"{indent}  📄 {f} ({tamaño//1024} KB)")
    if len(files) > 10:
        print(f"{indent}  ... y {len(files)-10} archivos más")