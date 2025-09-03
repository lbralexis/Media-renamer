import streamlit as st
import os
import re
from io import BytesIO
from zipfile import ZipFile

st.set_page_config(page_title="BatchName", page_icon="🧼", layout="wide")
st.title("BatchName")

# --- Champ unique : "Base (SAP-Titre)" ---
base_input = st.text_input("Base (colle ici : SAP-Titre)", placeholder="Ex : 252798-AppleWatch")
start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader("Sélectionner les fichiers", type=None, accept_multiple_files=True)

zip_bytes = None
zip_name = "fichiers_renommes.zip"
prepared = []

# --- Parse/validation du champ unique ---
# On attend : 6 chiffres, puis éventuellement '-', puis le titre
m = re.match(r"^\s*(\d{6})(?:-(.+))?\s*$", base_input or "")
sap_code = None
title = None
if m:
    sap_code = m.group(1)                   # "252798"
    title = (m.group(2) or "").strip()      # "AppleWatch" (ou "" si pas fourni)

if uploaded_files and sap_code:
    if not title:
        st.warning("Le champ ne contient que le code SAP. Tu peux coller au format `SAP-Titre` pour inclure le titre (ex : 252798-AppleWatch).")
    st.markdown("### Preview des fichiers renommés")
    cols = st.columns(5)
    start_idx = int(start_number)

    prepared = []
    for idx, file in enumerate(uploaded_files, start=start_idx):
        ext = os.path.splitext(file.name)[1]
        # Logique : SAP - <numéro> - Titre (si présent)
        if title:
            new_name = f"{sap_code}-{idx}-{title}{ext}"
        else:
            new_name = f"{sap_code}-{idx}{ext}"
        data = file.getvalue()
        prepared.append((new_name, data, ext))

    # Preview en grille
    for i, (new_name, data, ext) in enumerate(prepared):
        with cols[i % 5]:
            if ext.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                st.image(data, caption=new_name, use_container_width=True)
            else:
                st.text(f"📄 {new_name}")

    # ZIP en mémoire
    buf = BytesIO()
    with ZipFile(buf, 'w') as zipf:
        for new_name, data, _ in prepared:
            zipf.writestr(new_name, data)
    zip_bytes = buf.getvalue()

    # Nom du ZIP : SAP-Titre.zip si titre, sinon SAP.zip
    zip_name = f"{sap_code}-{title}.zip" if title else f"{sap_code}.zip"

elif uploaded_files and base_input and not sap_code:
    st.error("Format invalide. Utilise : 6 chiffres, puis un tiret et le titre (ex : 252798-AppleWatch).")

# --- Téléchargements centrés ---
if zip_bytes is not None:
    _, center, _ = st.columns([2, 4, 2])  # centrer au milieu
    with center:
        st.markdown("## 📦 Tout télécharger")
        st.download_button(
            "⬇️ Télécharger tout en .zip",
            data=zip_bytes,
            file_name=zip_name,
            mime="application/zip",
            use_container_width=True
        )

        st.markdown("## 📂 Ou télécharger un par un")
        for new_name, data, _ in prepared:
            st.download_button(
                label=new_name,
                data=data,
                file_name=new_name,
                mime="application/octet-stream",
                use_container_width=True
            )
else:
    _, center, _ = st.columns([2, 4, 2])
    with center:
        st.button("⬇️ Télécharger", disabled=True, use_container_width=True)

# --- Footer ---
st.markdown(
    """
    <div style="text-align: center; margin-top: 50px; font-size: 14px; color: grey;">
        Made with 🩵
    </div>
    """,
    unsafe_allow_html=True
)

