import streamlit as st
import os
from zipfile import ZipFile

st.title("BatchName")

# Champs utilisateur
sap_code = st.text_input("Code SAP (uniquement chiffres)", "")
title = st.text_input("Titre du fichier", "")
start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader("Sélectionne tes fichiers", type=None, accept_multiple_files=True)

if uploaded_files and sap_code.isdigit() and title.strip():
    st.markdown("### 👀 Preview des fichiers renommés")
    for idx, file in enumerate(uploaded_files, start=start_number):
        ext = os.path.splitext(file.name)[1].lower()
        new_name = f"{sap_code}-{idx}-{title}{ext}"

        # Si image → affichage avec futur nom
        if ext in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
            st.image(file, caption=new_name, width=200)
        else:
            st.text(f"📄 {new_name}")

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

        # Renommage avec format SAP-Numéro-Titre
        for i, file in enumerate(uploaded_files, start=start_number):
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
