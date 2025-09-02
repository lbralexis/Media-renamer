import streamlit as st
import os
import base64
from zipfile import ZipFile
from io import BytesIO

st.set_page_config(page_title="Nom’Propre", page_icon="🧼", layout="wide")
st.title("🧼 Nom’Propre — Prévisualise, réordonne, renomme")

# ---------- Helpers ----------
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

def to_base64(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode()

def guess_mime(ext: str) -> str:
    e = ext.lower()
    if e in {".jpg", ".jpeg"}: return "image/jpeg"
    if e == ".png": return "image/png"
    if e == ".gif": return "image/gif"
    if e == ".bmp": return "image/bmp"
    if e == ".webp": return "image/webp"
    return "application/octet-stream"

def build_new_name(sap: str, idx: int, title: str, ext: str) -> str:
    # Format: SAP-Numéro-Titre.ext
    return f"{sap}-{idx}-{title}{ext}"

def ensure_state():
    if "items" not in st.session_state:
        st.session_state.items = []  # list[dict]: {id, orig_name, ext, bytes, order}
    if "order_dirty" not in st.session_state:
        st.session_state.order_dirty = False

ensure_state()

# ---------- Inputs ----------
with st.sidebar:
    st.header("Paramètres")
    sap_code = st.text_input("Code SAP (uniquement chiffres)", "")
    title = st.text_input("Titre du fichier", "")
    start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader(
    "Sélectionne tes fichiers (images recommandées)",
    type=None,
    accept_multiple_files=True
)

# À l’upload, on stocke une structure stable en session
if uploaded_files:
    st.session_state.items = []
    for i, f in enumerate(uploaded_files, start=1):
        ext = os.path.splitext(f.name)[1]
        st.session_state.items.append({
            "id": f"item_{i}",
            "orig_name": f.name,
            "ext": ext,
            "bytes": f.read(),
            "order": i  # ordre initial = ordre d’upload (1..n)
        })

# ---------- Preview zone ----------
valid_inputs = sap_code.isdigit() and title.strip() and len(st.session_state.items) > 0

st.markdown("### 👀 Preview & ordre")
st.caption("Astuce : réorganise les vignettes (drag & drop) ou ajuste la colonne **Ordre** si le DnD n’est pas dispo.")

# Tente d’activer le drag & drop (composant communautaire). Sinon fallback.
drag_available = False
try:
    # streamlit-sortables
    from streamlit_sortables import sort_items
    drag_available = True
except Exception:
    drag_available = False

# Construit la liste d’items visuels pour DnD
def item_card_html(item, display_index):
    """Crée un bloc HTML (image + caption) pour le composant drag & drop."""
    ext = item["ext"].lower()
    is_img = ext in IMG_EXTS
    caption = build_new_name(sap_code if sap_code.isdigit() else "SAP",
                             display_index, title if title.strip() else "Titre",
                             ext if ext else "")
    if is_img:
        mime = guess_mime(ext)
        b64 = to_base64(item["bytes"])
        img_tag = f'<img src="data:{mime};base64,{b64}" style="width:100%;height:auto;border-radius:12px;">'
    else:
        # Icône “fichier” avec nom
        img_tag = '<div style="width:100%;height:120px;border:1px dashed #ddd;border-radius:12px;display:flex;align-items:center;justify-content:center;">📄</div>'
    return f"""
    <div class="np-card" style="width:100%;padding:8px;">
      <div style="box-shadow:0 2px 12px rgba(0,0,0,0.06);border-radius:12px;overflow:hidden;">
        {img_tag}
      </div>
      <div style="font-size:12px;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{caption}">
        {caption}
      </div>
    </div>
    """

# On travaille sur une copie triée par 'order'
items_sorted = sorted(st.session_state.items, key=lambda x: x["order"])
n = len(items_sorted)

# Présente en grille 5 colonnes + drag si dispo
if n > 0:
    # --------------- DRAG & DROP ---------------
    if drag_available:
        st.markdown(
            """
            <style>
            /* grille fluide 5 colonnes */
            .np-grid {display:flex;flex-wrap:wrap;gap:16px;}
            .np-grid > div {flex: 0 0 calc(20% - 12.8px);} /* ~5 colonnes */
            @media (max-width:1200px){ .np-grid > div {flex-basis: calc(25% - 12px);} } /* 4 col */
            @media (max-width:900px){ .np-grid > div {flex-basis: calc(33.33% - 11px);} } /* 3 col */
            @media (max-width:600px){ .np-grid > div {flex-basis: calc(50% - 8px);} } /* 2 col */
            </style>
            """,
            unsafe_allow_html=True
        )

        # Prépare les blocs HTML pour sort_items()
        display_blocks = []
        for idx, it in enumerate(items_sorted, start=int(start_number) if start_number else 1):
            display_blocks.append(item_card_html(it, idx))

        # Le composant renvoie les items réordonnés
        st.markdown('<div class="np-grid">', unsafe_allow_html=True)
        new_order = sort_items(
            display_blocks,
            direction="horizontal",  # permet le drag multi-lignes
            # group=True  # (selon version du composant; laissé simple ici)
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # new_order est la liste des blocs HTML réordonnés → on mappe vers nos items
        # Astuce : on les matche par la légende contenue (caption) n’étant pas fiable à 100%,
        # on se base sur l’ordre retourné (index) et on applique cet ordre à items_sorted.
        if isinstance(new_order, list) and len(new_order) == len(items_sorted):
            # On applique l’ordre retourné (positions)
            reordered = []
            for html_block in new_order:
                # retrouve l’index d’origine de ce block
                # (on compare le HTML brut; c’est acceptable pour un petit outil interne)
                for i, block in enumerate(display_blocks):
                    if block == html_block:
                        reordered.append(items_sorted[i])
                        break
            # Réécrit les orders 1..n (ou start_number..)
            start_idx = int(start_number) if start_number else 1
            for k, it in enumerate(reordered, start=start_idx):
                it["order"] = k
            st.session_state.items = sorted(reordered, key=lambda x: x["order"])
    # --------------- FALLBACK NUMERIQUE ---------------
    if not drag_available:
        st.info("Le drag & drop n’est pas disponible sur cet environnement. Réordonne via la colonne **Ordre** ci-dessous.")
        import pandas as pd
        df = pd.DataFrame([
            {"Ordre": it["order"], "Nom original": it["orig_name"]}
            for it in items_sorted
        ])
        edited = st.data_editor(
            df,
            num_rows="fixed",
            use_container_width=True,
            column_config={
                "Ordre": st.column_config.NumberColumn(step=1, min_value=1, max_value=n)
            }
        )
        # Applique le nouvel ordre
        new_orders = list(edited["Ordre"].astype(int))
        # Si doublons ou trous, on normalise
        if len(set(new_orders)) != n or min(new_orders) != 1:
            # normalisation simple: on remappe dans l’ordre d’apparition
            new_orders = list(range(1, n+1))
        for it, new_o in zip(items_sorted, new_orders):
            it["order"] = new_o
        st.session_state.items = sorted(items_sorted, key=lambda x: x["order"])

# ---------- Grille preview finale (5 colonnes) ----------
if len(st.session_state.items) > 0 and valid_inputs:
    st.markdown("#### 📸 Aperçu (après réordonnancement)")
    cols = st.columns(5)
    start_idx = int(start_number)
    for i, it in enumerate(st.session_state.items, start=0):
        ext = it["ext"]
        is_img = ext.lower() in IMG_EXTS
        num = start_idx + i
        new_name = build_new_name(sap_code, num, title, ext)
        with cols[i % 5]:
            if is_img:
                st.image(BytesIO(it["bytes"]), caption=new_name, use_column_width=True)
            else:
                st.write(f"📄 {new_name}")

# ---------- Action: Renommer & Télécharger ----------
st.markdown("---")
go = st.button("✅ Renommer & Télécharger", use_container_width=True)
if go:
    if not sap_code.isdigit():
        st.error("⚠️ Le code SAP doit contenir uniquement des chiffres.")
    elif not title.strip():
        st.error("⚠️ Le titre du fichier ne peut pas être vide.")
    elif len(st.session_state.items) == 0:
        st.warning("⚠️ Merci de sélectionner des fichiers.")
    else:
        output_dir = "renamed_files"
        os.makedirs(output_dir, exist_ok=True)

        # On suit l’ordre actuel (déjà trié par 'order')
        files_now = sorted(st.session_state.items, key=lambda x: x["order"])
        start_idx = int(start_number)
        for i, it in enumerate(files_now, start=0):
            num = start_idx + i
            new_name = build_new_name(sap_code, num, title, it["ext"])
            with open(os.path.join(output_dir, new_name), "wb") as f:
                f.write(it["bytes"])

        # Zip téléchargeable
        zip_path = "fichiers_renommes.zip"
        with ZipFile(zip_path, 'w') as zipf:
            for f in os.listdir(output_dir):
                zipf.write(os.path.join(output_dir, f), f)

        with open(zip_path, "rb") as f:
            st.download_button("⬇️ Télécharger le zip", f, file_name="fichiers_renommes.zip")
