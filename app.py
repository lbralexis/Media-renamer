import streamlit as st
import os, base64, re
from io import BytesIO
from zipfile import ZipFile
from unidecode import unidecode

st.set_page_config(page_title="Nom’Propre", page_icon="🧼", layout="wide")
st.title("🧼 Nom’Propre — Prévisualise, réordonne, renomme")

IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

def ensure_state():
    if "file_list" not in st.session_state or not isinstance(st.session_state["file_list"], list):
        st.session_state["file_list"] = []
ensure_state()

def sanitize_title(txt: str) -> str:
    txt = unidecode(txt).strip().lower()
    txt = re.sub(r"\s+", "-", txt)
    txt = re.sub(r"[^a-z0-9\-]+", "", txt)
    txt = re.sub(r"-{2,}", "-", txt).strip("-")
    return txt or "titre"

def build_new_name(sap: str, num: str | int, title: str, ext: str) -> str:
    return f"{sap}-{num}-{title}{ext}"

def guess_mime(ext: str) -> str:
    e = ext.lower()
    return {
        ".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",
        ".gif":"image/gif",".bmp":"image/bmp",".webp":"image/webp"
    }.get(e, "application/octet-stream")

with st.sidebar:
    st.header("Paramètres")
    sap_code = st.text_input("Code SAP (uniquement chiffres)", "")
    title_raw = st.text_input("Titre du fichier", "")
    start_number = st.number_input("Numéro de départ", value=1, step=1)
    pad_len = st.number_input("Padding des numéros (ex. 3 → 001)", min_value=0, value=0, step=1)

uploaded_files = st.file_uploader(
    "Sélectionne tes fichiers (images recommandées)",
    type=None,
    accept_multiple_files=True
)

# Remplir l'état à chaque nouvel upload (ordre initial = ordre d'upload)
if uploaded_files:
    st.session_state["file_list"] = []
    for i, f in enumerate(uploaded_files, start=1):
        ext = os.path.splitext(f.name)[1]
        st.session_state["file_list"].append({
            "id": f"item_{i}",
            "orig_name": f.name,
            "ext": ext,
            "bytes": f.read(),
            "order": i
        })

# Tri sécurisé
files_sorted = sorted(
    st.session_state.get("file_list", []),
    key=lambda x: x.get("order", 0)
)

valid_inputs = sap_code.isdigit() and title_raw.strip() and len(files_sorted) > 0
title_clean = sanitize_title(title_raw)

st.markdown("### 👀 Preview & ordre")

# Drag & drop si dispo, sinon fallback
drag_available = False
try:
    from streamlit_sortables import sort_items
    drag_available = True
except Exception:
    drag_available = False

def make_card_html(item, disp_index):
    ext = item["ext"].lower()
    is_img = ext in IMG_EXTS
    caption = build_new_name(
        sap_code if sap_code.isdigit() else "sap",
        str(disp_index).zfill(pad_len) if pad_len else disp_index,
        title_clean or "titre",
        ext
    )
    if is_img:
        b64 = base64.b64encode(item["bytes"]).decode()
        html_img = f'<img src="data:{guess_mime(ext)};base64,{b64}" style="width:100%;height:auto;border-radius:12px;">'
    else:
        html_img = '<div style="width:100%;height:120px;border:1px dashed #ddd;border-radius:12px;display:flex;align-items:center;justify-content:center;">📄</div>'
    return f"""
    <div style="width:100%;padding:8px;">
      <div style="box-shadow:0 2px 12px rgba(0,0,0,0.06);border-radius:12px;overflow:hidden;">
        {html_img}
      </div>
      <div style="font-size:12px;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{caption}">
        {caption}
      </div>
    </div>
    """

n = len(files_sorted)
if n:
    start_idx = int(start_number)
    if drag_available:
        st.markdown("""
        <style>
        .np-grid {display:flex;flex-wrap:wrap;gap:16px;}
        .np-grid > div {flex: 0 0 calc(20% - 12.8px);} /* 5 colonnes */
        @media (max-width:1200px){ .np-grid > div {flex-basis: calc(25% - 12px);} }  /* 4 */
        @media (max-width:900px){ .np-grid > div {flex-basis: calc(33.33% - 11px);} } /* 3 */
        @media (max-width:600px){ .np-grid > div {flex-basis: calc(50% - 8px);} }     /* 2 */
        </style>
        """, unsafe_allow_html=True)

        blocks = [make_card_html(it, (start_idx+i)) for i, it in enumerate(files_sorted)]
        st.markdown('<div class="np-grid">', unsafe_allow_html=True)
        new_blocks = sort_items(blocks, direction="horizontal")
        st.markdown('</div>', unsafe_allow_html=True)

        if isinstance(new_blocks, list) and len(new_blocks) == len(blocks):
            reordered = []
            for nb in new_blocks:
                idx = blocks.index(nb)
                reordered.append(files_sorted[idx])
            for k, it in enumerate(reordered, start=start_idx):
                it["order"] = k
            st.session_state["file_list"] = sorted(reordered, key=lambda x: x.get("order", 0))
            files_sorted = st.session_state["file_list"][:]
    else:
        st.info("Drag & drop indisponible ici. Modifie l’**Ordre** dans le tableau ci-dessous.")
        import pandas as pd
        df = pd.DataFrame([{"Ordre": it.get("order", i+1), "Nom original": it["orig_name"]}
                           for i, it in enumerate(files_sorted)])
        edited = st.data_editor(
            df, num_rows="fixed", use_container_width=True,
            column_config={"Ordre": st.column_config.NumberColumn(step=1, min_value=1, max_value=n)}
        )
        new_orders = list(edited["Ordre"].astype(int))
        if len(set(new_orders)) != n or min(new_orders) != 1:
            new_orders = list(range(1, n+1))
        for it, new_o in zip(files_sorted, new_orders):
            it["order"] = new_o
        st.session_state["file_list"] = sorted(files_sorted, key=lambda x: x.get("order", 0))
        files_sorted = st.session_state["file_list"][:]

# Aperçu final (5 colonnes)
if valid_inputs:
    st.markdown("#### 📸 Aperçu (après réordonnancement)")
    cols = st.columns(5)
    for i, it in enumerate(files_sorted):
        num_int = int(start_number) + i
        num = str(num_int).zfill(pad_len) if pad_len else num_int
        ext = it["ext"]
        name = build_new_name(sap_code, num, title_clean, ext)
        with cols[i % 5]:
            if ext.lower() in IMG_EXTS:
                st.image(BytesIO(it["bytes"]), caption=name, use_column_width=True)
            else:
                st.write(f"📄 {name}")

st.markdown("---")
if st.button("✅ Renommer & Télécharger", use_container_width=True):
    if not sap_code.isdigit():
        st.error("⚠️ Le code SAP doit contenir uniquement des chiffres.")
    elif not title_raw.strip():
        st.error("⚠️ Le titre du fichier ne peut pas être vide.")
    elif not files_sorted:
        st.warning("⚠️ Merci de sélectionner des fichiers.")
    else:
        out_dir = "renamed_files"
        os.makedirs(out_dir, exist_ok=True)
        for i, it in enumerate(files_sorted):
            num_int = int(start_number) + i
            num = str(num_int).zfill(pad_len) if pad_len else num_int
            new_name = build_new_name(sap_code, num, title_clean, it["ext"])
            with open(os.path.join(out_dir, new_name), "wb") as f:
                f.write(it["bytes"])
        zip_path = "fichiers_renommes.zip"
        with ZipFile(zip_path, "w") as z:
            for f in os.listdir(out_dir):
                z.write(os.path.join(out_dir, f), f)
        with open(zip_path, "rb") as f:
            st.download_button("⬇️ Télécharger le zip", f, file_name="fichiers_renommes.zip")
