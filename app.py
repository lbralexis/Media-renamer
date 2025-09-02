import streamlit as st
import os
from io import BytesIO
from zipfile import ZipFile
import pandas as pd

st.set_page_config(page_title="Nom’Propre", page_icon="🧼", layout="wide")
st.title("📂 Nom’Propre – L'outil de renommage")

# ---------- ÉTAT ----------
if "file_list" not in st.session_state:
    # Chaque item: {id, orig_name, ext, bytes, order}
    st.session_state.file_list = []

def load_files(uploaded_files):
    st.session_state.file_list = []
    for i, f in enumerate(uploaded_files, start=1):
        name, ext = os.path.splitext(f.name)
        st.session_state.file_list.append({
            "id": f"item_{i}",
            "orig_name": f.name,
            "ext": ext,
            "bytes": f.read(),
            "order": i
        })

def current_sorted():
    return sorted(st.session_state.file_list, key=lambda x: x["order"])

# ---------- PARAMS ----------
colA, colB, colC = st.columns([1, 1, 1])
with colA:
    sap_code = st.text_input("Code SAP (uniquement chiffres)", "")
with colB:
    title = st.text_input("Titre du fichier", "")
with colC:
    start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader(
    "Sélectionne tes fichiers",
    type=None,
    accept_multiple_files=True
)

# Charger en mémoire à chaque nouvel upload
if uploaded_files:
    load_files(uploaded_files)

files = current_sorted()

# ---------- TABLEAU D’ORDRE ----------
if len(files) > 0:
    # Prépare DF (ordre courant + nouveaux noms)
    start_idx = int(start_number)
    rows = []
    for i, it in enumerate(files):
        num = start_idx + i
        new_name = f"{sap_code}-{num}-{title}{it['ext']}" if sap_code.isdigit() and title.strip() else ""
        rows.append({
            "Sel": False,
            "Ordre": it["order"],
            "Nom original": it["orig_name"],
            "Nouveau nom": new_name,
            "_id": it["id"],  # caché/technique
        })
    df = pd.DataFrame(rows)

    st.subheader("🧭 Ordonnancement")
    c1, c2, c3, c4 = st.columns([1,1,1,3])
    with c1:
        move_up = st.button("⬆️ Monter sélection")
    with c2:
        move_down = st.button("⬇️ Descendre sélection")
    with c3:
        apply_numbers = st.button("✔️ Appliquer les rangs saisis")

edited = st.data_editor(
    df,
    use_container_width=True,
    hide_index=True,
    num_rows="fixed",
    column_config={
        "Sel": st.column_config.CheckboxColumn(help="Sélectionner des lignes à déplacer"),
        "Ordre": st.column_config.NumberColumn(step=1, min_value=1, help="Modifier pour imposer un rang"),
        "Nom original": st.column_config.TextColumn(disabled=True),
        "Nouveau nom": st.column_config.TextColumn(disabled=True),
        "_id": st.column_config.TextColumn(disabled=True),
    }
)

# --- Actions sur l’ordre ---
# 1) Appliquer les valeurs saisies dans "Ordre"
if apply_numbers:
    tmp = edited.sort_values(by=["Ordre", "Nom original"]).reset_index(drop=True)
    for idx, row in tmp.iterrows():
        _id = row["_id"]
        st.session_state.file_list = [
            {**it, "order": (idx + start_idx)} if it["id"] == _id else it
            for it in st.session_state.file_list
        ]

    # 2) Monter / Descendre la sélection (swap progressif, garde l’ordre interne)
    selected_ids = [row["_id"] for _, row in edited.iterrows() if row["Sel"]]

    if selected_ids and (move_up or move_down):
        # Liste ordonnée actuelle (par position)
        ordered_ids = [it["id"] for it in current_sorted()]
        selected_set = set(selected_ids)

        if move_up:
            # Parcourt de haut en bas: chaque élément sélectionné échange avec le précédent non-sélectionné
            i = 1
            while i < len(ordered_ids):
                if ordered_ids[i] in selected_set and ordered_ids[i-1] not in selected_set:
                    ordered_ids[i-1], ordered_ids[i] = ordered_ids[i], ordered_ids[i-1]
                    if i > 1:
                        i -= 1
                else:
                    i += 1

        if move_down:
            # Parcourt de bas en haut: chaque élément sélectionné échange avec le suivant non-sélectionné
            i = len(ordered_ids) - 2
            while i >= 0:
                if ordered_ids[i] in selected_set and ordered_ids[i+1] not in selected_set:
                    ordered_ids[i], ordered_ids[i+1] = ordered_ids[i+1], ordered_ids[i]
                    if i < len(ordered_ids) - 2:
                        i += 1
                else:
                    i -= 1

        # Réécrit les orders  (start_number..)
        for idx, _id in enumerate(ordered_ids, start=start_idx):
            st.session_state.file_list = [
                {**it, "order": idx} if it["id"] == _id else it
                for it in st.session_state.file_list
            ]

    # --------- PREVIEW : grille 5 colonnes ----------
    files = current_sorted()
    if sap_code.isdigit() and title.strip():
        st.subheader("👀 Preview (après ordonnancement)")
        cols = st.columns(5)
        for i, it in enumerate(files):
            num = start_idx + i
            new_name = f"{sap_code}-{num}-{title}{it['ext']}"
            with cols[i % 5]:
                if it["ext"].lower() in [".png",".jpg",".jpeg",".gif",".bmp",".webp"]:
                    st.image(BytesIO(it["bytes"]), caption=new_name, use_container_width=True)
                else:
                    st.text(f"📄 {new_name}")

# ---------- RENOMMER & TÉLÉCHARGER ----------
st.markdown("---")
if st.button("✅ Renommer & Télécharger", use_container_width=True):
    if not sap_code.isdigit():
        st.error("⚠️ Le code SAP doit contenir uniquement des chiffres.")
    elif not title.strip():
        st.error("⚠️ Le titre du fichier ne peut pas être vide.")
    elif len(st.session_state.file_list) == 0:
        st.warning("⚠️ Merci de sélectionner des fichiers.")
    else:
        out_dir = "renamed_files"
        os.makedirs(out_dir, exist_ok=True)

        files = current_sorted()
        start_idx = int(start_number)
        for i, it in enumerate(files):
            num = start_idx + i
            new_name = f"{sap_code}-{num}-{title}{it['ext']}"
            with open(os.path.join(out_dir, new_name), "wb") as f:
                f.write(it["bytes"])

        zip_path = "fichiers_renommes.zip"
        with ZipFile(zip_path, "w") as z:
            for f in os.listdir(out_dir):
                z.write(os.path.join(out_dir, f), f)

        with open(zip_path, "rb") as f:
            st.download_button("⬇️ Télécharger le zip", f, file_name="fichiers_renommes.zip")
