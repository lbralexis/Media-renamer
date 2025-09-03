import streamlit as st
import os, re
from io import BytesIO
from zipfile import ZipFile

st.set_page_config(page_title="BatchName", page_icon="🧼", layout="wide")
st.title("BatchName")

# ---------- Helpers ----------
def parse_base(s: str):
    """Attend '######-Titre' ou juste '######' (6 chiffres)."""
    m = re.match(r"^\s*(\d{6})(?:-(.+))?\s*$", s or "")
    if not m: 
        return None, None
    sap = m.group(1)
    title = (m.group(2) or "").strip()
    return sap, title

def build_name(sap: str, num: int, title: str, ext: str):
    return f"{sap}-{num}-{title}{ext}" if title else f"{sap}-{num}{ext}"

# ---------- État ----------
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

def get_sorted():
    return sorted(st.session_state.file_list, key=lambda x: x["order"])

# ---------- Entrées ----------
base_input = st.text_input("Base (colle ici : SAP-Titre)", placeholder="Ex : 252798-AppleWatch")
start_number = st.number_input("Numéro de départ", value=1, step=1)

uploaded_files = st.file_uploader("Sélectionner les fichiers", type=None, accept_multiple_files=True)
if uploaded_files:
    load_files(uploaded_files)

sap_code, title = parse_base(base_input)
files = get_sorted()

zip_bytes = None
prepared = []

# ---------- Ordonnancement (flèches) + Preview ----------
if files and sap_code:
    st.markdown("### Preview & ordonnancement")
    start_idx = int(start_number)

    # Ligne d'entête
    hdr = st.columns([6, 2, 1, 1])
    hdr[0].markdown("**Nom original**")
    hdr[1].markdown("**Nouveau nom**")
    hdr[2].markdown("**⬆️**")
    hdr[3].markdown("**⬇️**")

    # Pour chaque ligne, boutons Monter/Descendre
    for pos, it in enumerate(files):
        num = start_idx + pos
        new_name = build_name(sap_code, num, title or "", it["ext"])

        c1, c2, c3, c4 = st.columns([6, 2, 1, 1])
        c1.write(it["orig_name"])
        c2.write(new_name)

        up_key = f"up_{it['id']}"
        down_key = f"down_{it['id']}"

        # Désactiver si déjà en haut/bas
        up_pressed = c3.button("Monter", key=up_key, disabled=(pos == 0))
        down_pressed = c4.button("Descendre", key=down_key, disabled=(pos == len(files)-1))

        # Appliquer le swap dès qu'on clique
        if up_pressed and pos > 0:
            files[pos]["order"], files[pos-1]["order"] = files[pos-1]["order"], files[pos]["order"]
            st.session_state.file_list = get_sorted()
            st.rerun()

        if down_pressed and pos < len(files)-1:
            files[pos]["order"], files[pos+1]["order"] = files[pos+1]["order"], files[pos]["order"]
            st.session_state.file_list = get_sorted()
            st.rerun()

    st.divider()

    # Preview vignettes (5 colonnes) recalculée avec l'ordre courant
    st.markdown("#### Aperçu visuel")
    cols = st.columns(5)
    files = get_sorted()
    prepared = []
    for i, it in enumerate(files):
        num = start_idx + i
        new_name = build_name(sap_code, num, title or "", it["ext"])
        prepared.append((new_name, it["bytes"], it["ext"]))
        with cols[i % 5]:
            if it["ext"].lower() in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"]:
                st.image(it["bytes"], caption=new_name, use_container_width=True)
            else:
                st.text(f"📄 {new_name}")

    # Construire le ZIP en mémoire
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
