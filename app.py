import streamlit as st
import os
from io import BytesIO
from zipfile import ZipFile

st.set_page_config(page_title="BatchName", page_icon="🧼", layout="wide")
st.title("BatchName")

# Champs utilisateur
sap_code = st.text_input("Code SAP", "")
title = st.text_input("Libellé produit", "")
start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader("Sélectionner les fichiers", type=None, accept_multiple_files=True)

zip_bytes = None
zip_name = "fichiers_renommes.zip"

if uploaded_files and sap_code.isdigit() and title.strip():
    st.markdown("Preview des fichiers renommés")
    cols = st.columns(5)
    start_idx = int(start_number)

    prepared = []
    for idx, file in enumerate(uploaded_files, start=start_idx):
        ext = os.path.splitext(file.name)[1]
        new_name = f"{sap_code}-{idx}-{title}{ext}"
        data = file.getvalue()
        prepared.append((new_name, data, ext))

    for i, (new_name, data, ext) in enumerate(prepared):
        with cols[i % 5]:
            if ext.lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                st.image(data, caption=new_name, use_container_width=True)
            else:
                st.text(f"📄 {new_name}")

    buf = BytesIO()
    with ZipFile(buf, 'w') as zipf:
        for new_name, data, _ in prepared:
            zipf.writestr(new_name, data)
    zip_bytes = buf.getvalue()

    zip_name = f"{sap_code}-{title}.zip"

if zip_bytes is not None:
    st.download_button(
        "Renommer & Télécharger",
        data=zip_bytes,
        file_name=zip_name,
        mime="application/zip",
        use_container_width=True
    )
else:
    st.button("Renommer & Télécharger", disabled=True, use_container_width=True)


st.markdown(
    """
    <div style="text-align: center; margin-top: 50px; font-size: 14px; color: grey;">
        Made with 🩵</b>
    </div>
    """,
    unsafe_allow_html=True
)
