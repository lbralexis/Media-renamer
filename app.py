import streamlit as st
import os
from io import BytesIO
from zipfile import ZipFile

st.title("📂 Nom’Propre – L'outil de renommage")

# Champs utilisateur
sap_code = st.text_input("Code SAP (uniquement chiffres)", "")
title = st.text_input("Titre du fichier", "")
start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader("Sélectionne tes fichiers", type=None, accept_multiple_files=True)

# On ne calcule le zip que si tout est prêt
zip_bytes = None

if uploaded_files and sap_code.isdigit() and title.strip():
    st.markdown("### 👀 Preview des fichiers renommés")
    cols = st.columns(5)  # 5 images par ligne
    start_idx = int(start_number)

    # Prépare une liste (nouveau_nom, bytes, ext) pour preview + zip
    prepared = []
    for idx, file in enumerate(uploaded_files, start=start_idx):
        ext = os.path.splitext(file.name)[1]
        new_name = f"{sap_code}-{idx}-{title}{ext}"
        data = file.getvalue()  # bytes du fichier (safe pour preview + zip)
        prepared.append((new_name, data, ext))

    # Preview
    for i, (new_name, data, ext) in enumerate(prepared):
        with cols[i % 5]:
            if ext.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                st.image(data, caption=new_name, use_container_width=True)
            else:
                st.text(f"📄 {new_name}")

    # Construire le zip en mémoire (une seule fois)
    buf = BytesIO()
    with ZipFile(buf, 'w') as zipf:
        for new_name, data, _ in prepared:
            zipf.writestr(new_name, data)
    zip_bytes = buf.getvalue()

# --- Un seul bouton pour télécharger directement ---
if zip_bytes is not None:
    st.download_button(
        "✅ Renommer & Télécharger (.zip)",
        data=zip_bytes,
        file_name="fichiers_renommes.zip",
        mime="application/zip",
        use_container_width=True
    )
else:
    st.button("✅ Renommer & Télécharger (.zip)", disabled=True, use_container_width=True)
