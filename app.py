import streamlit as st
import os, re, base64
from io import BytesIO
from zipfile import ZipFile

st.set_page_config(page_title="BatchName", page_icon="🧼", layout="wide")
st.title("BatchName")

# ---------- Helpers ----------
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}

def parse_base(s: str):
    """Attend '######-Titre' ou juste '######' (6 chiffres)."""
    m = re.match(r"^\s*(\d{6})(?:-(.+))?\s*$", s or "")
    if not m: return None, None
    sap = m.group(1)
    title = (m.group(2) or "").strip()
    return sap, title

def build_name(sap: str, num: int, title: str, ext: str):
    return f"{sap}-{num}-{title}{ext}" if title else f"{sap}-{num}{ext}"

def guess_mime(ext: str):
    e = ext.lower()
    return {
        ".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",
        ".gif":"image/gif",".bmp":"image/bmp",".webp":"image/webp"
    }.get(e, "application/octet-stream")

def ensure_state():
    if "file_list" not in st.session_state or not isinstance(st.session_state["file_list"], list):
        st.session_state["file_list"] = []
ensure_state()

# ---------- Entrées ----------
base_input = st.text_input("Base (colle ici : SAP-Titre)", placeholder="Ex : 252798-AppleWatch")
start_number = st.number_input("Numéro de départ", value=1, step=1)
uploaded_files = st.file_uploader("Sélectionner les fichiers", type=None, accept_multiple_files=True)

sap_code, title = parse_base(base_input)
start_idx = int(start_number)

# Charger en mémoire si upload
if uploaded_files:
    st.session_state["file_list"] = []
    for i, f in enumerate(uploaded_files, start=1):
        name, ext = os.path.splitext(f.name)
        st.session_state["file_list"].append({
            "id": f"item_{i}",
            "orig_name": f.name,
            "ext": ext,
            "bytes": f.read(),
            "order": i
        })

files = sorted(st.session_state["file_list"], key=lambda x: x["order"])
zip_bytes = None
prepared = []

# ---------- Preview + Drag & Drop ----------
if files and sap_code:
    st.markdown("### Preview & réordonnancement")

    # Tente d'importer le composant DnD
    drag_available = False
    try:
        from streamlit_sortables import sort_items
        drag_available = True
    except Exception:
        drag_available = False

    def card_html(item, display_num):
        ext = item["ext"].lower()
        is_img = ext in IMG_EXTS
        name = build_name(sap_code, display_num, title or "", item["ext"])
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
          <div style="font-size:12px;margin-top:6px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" title="{name}">
            {name}
          </div>
        </div>
        """

    # Grille responsive 5 colonnes
    st.markdown("""
    <style>
    .np-grid {display:flex;flex-wrap:wrap;gap:16px;}
    .np-grid > div {flex: 0 0 calc(20% - 12.8px);} /* 5 colonnes */
    @media (max-width:1200px){ .np-grid > div {flex-basis: calc(25% - 12px);} }  /* 4 */
    @media (max-width:900px){ .np-grid > div {flex-basis: calc(33.33% - 11px);} } /* 3 */
    @media (max-width:600px){ .np-grid > div {flex-basis: calc(50% - 8px);} }     /* 2 */
    </style>
    """, unsafe_allow_html=True)

    if drag_available:
        # Construire les blocs HTML dans l'ordre actuel
        blocks = [card_html(it, start_idx + i) for i, it in enumerate(files)]
        st.markdown('<div class="np-grid">', unsafe_allow_html=True)
        new_blocks = sort_items(blocks, direction="horizontal")
        st.markdown('</div>', unsafe_allow_html=True)

        # Si l'utilisateur a réordonné, refléter dans l'état
        if isinstance(new_blocks, list) and len(new_blocks) == len(blocks):
            reordered = []
            for nb in new_blocks:
                idx = blocks.index(nb)
                reordered.append(files[idx])
            # réécrire les orders (start ..)
            for i, it in enumerate(reordered, start=start_idx):
                it["order"] = i
            st.session_state["file_list"] = sorted(reordered, key=lambda x: x["order"])
            files = st.session_state["file_list"][:]
    else:
        # Fallback : petit tableau Ordre éditable
        st.info("Drag & drop indisponible ici. Modifie la colonne **Ordre** ci-dessous.")
        import pandas as pd
        df = pd.DataFrame([{"Ordre": it["order"], "Nom original": it["orig_name"]} for it in files])
        edited = st.data_editor(
            df, num_rows="fixed", use_container_width=True,
            column_config={"Ordre": st.column_config.NumberColumn(step=1, min_value=1, max_value=len(files))}
        )
        # Normaliser 1..N (à partir de start_idx pour les noms)
        new_orders = list(edited["Ordre"].astype(int))
        if len(set(new_orders)) != len(files):
            new_orders = list(range(1, len(files) + 1))
        for it, new_o in zip(files, new_orders):
            it["order"] = new_o
        st.session_state["file_list"] = sorted(files, key=lambda x: x["order"])
        files = st.session_state["file_list"][:]

    # Construire la liste finale (après DnD / édition)
    files = sorted(files, key=lambda x: x["order"])
    prepared = []
    for i, it in enumerate(files):
        num = start_idx + i  # renumérotation compacte
        new_name = build_name(sap_code, num, title or "", it["ext"])
        prepared.append((new_name, it["bytes"], it["ext"]))

    # Aperçu en grille recalculé (avec noms à jour)
    st.markdown("#### Aperçu après réordonnancement")
    cols = st.columns(5)
    for i, (new_name, data, ext) in enumerate(prepared):
        with cols[i % 5]:
            if ext.lower() in IMG_EXTS:
                st.image(data, caption=new_name, use_container_width=True)
            else:
                st.text(f"📄 {new_name}")

    # ZIP en mémoire
    buf = BytesIO()
    with ZipFile(buf, 'w') as zipf:
        for new_name, data, _ in prepared:
            zipf.writestr(new_name, data)
    zip_bytes = buf.getvalue()
    zip_name = f"{sap_code}-{(title or '').strip()}.zip" if title else f"{sap_code}.zip"

elif uploaded_files and base_input and not sap_code:
    st.error("Format invalide. Utilise : 6 chiffres, puis un tiret et le titre (ex : 252798-AppleWatch).")

# ---------- Téléchargements centrés ----------
if zip_bytes:
    _, center, _ = st.columns([2, 4, 2])
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

# ---------- Footer ----------
st.markdown(
    """
    <div style="text-align: center; margin-top: 50px; font-size: 14px; color: grey;">
        Made with 🩵
    </div>
    """,
    unsafe_allow_html=True
)

