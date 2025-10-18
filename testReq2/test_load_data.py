from utils.load_data import load_bib_data

print("📚 Cargando datos...")

df = load_bib_data()

print("✅ Datos cargados correctamente.\n")
print(df.head())

print(f"\nTotal de artículos cargados: {len(df)}")
