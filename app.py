import streamlit as st
import os
from zipfile import ZipFile

st.title("📂 Nom’Propre – L'outil de renommage")

# Champs utilisateur
sap_code = st.text_input("Code SAP (uniquement chiffres)", "")
title = st.text_input("Titre du fichier", "")
start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader("Sélectionne tes fichiers", type=None, accept_multiple_files=True)

# --- Preview ---
if uploaded_files and sap_code.isdigit() and title.strip():
    st.markdown("### 👀 Preview des fichiers renommés")
    cols = st.columns(5)  # 5 images par ligne
    start_idx = int(start_number)
    for idx, file in enumerate(uploaded_files, start=start_idx):
        ext = os.path.splitext(file.name)[1]
        new_name = f"{sap_code}-{idx}-{title}{ext}"

        with cols[(idx - start_idx) % 5]:  # affiche en grille
            if ext.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                st.image(file, caption=new_name, use_container_width=True)
            else:
                st.text(f"📄 {new_name}")

# --- Renommer & Télécharger ---
if st.button("Renommer & Télécharger"):
    if not sap_code.isdigit():
        st.error("⚠️ Le code SAP doit contenir uniquement des chiffres.")
    elif not title.strip():
        st.error("⚠️ Le titre du fichier ne peut pas être vide.")
    elif not uploaded_files:
        st.warning("⚠️ Merci de sélectionner des fichiers.")
    else:
        output_dir = "renamed_files"
        os.makedirs(output_dir, exist_ok=True)

        start_idx = int(start_number)
        # Renommage avec format SAP-Numéro-Titre
        for i, file in enumerate(uploaded_files, start=start_idx):
            ext = os.path.splitext(file.name)[1]
            new_name = f"{sap_code}-{i}-{title}{ext}"
            new_path = os.path.join(output_dir, new_name)
            with open(new_path, "wb") as f:
                f.write(file.read())

        # Création du zip
        zip_path = "fichiers_renommes.zip"
        with ZipFile(zip_path, 'w') as zipf:
            for f in os.listdir(output_dir):
                zipf.write(os.path.join(output_dir, f), f)

        with open(zip_path, "rb") as f:
            st.download_button("⬇️ Télécharger le zip", f, file_name="fichiers_renommes.zip")
