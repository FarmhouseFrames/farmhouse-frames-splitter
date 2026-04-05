import streamlit as st
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import zipfile

# --- PAGE SETUP ---
st.set_page_config(page_title="Farmhouse Frames Designer", layout="wide")

st.title("🖼️ Farmhouse Frames: Professional Splitter")
st.write("Designed for Kristin Canada | Cadiz Photography Production")

# 1. Image Loading Logic
img_source = st.sidebar.radio("Image Source", ["Upload Local File", "URL"])
image = None

if img_source == "URL":
    url = st.sidebar.text_input("Paste Image URL (Direct link to JPG)")
    if url:
        try:
            response = requests.get(url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
        except:
            st.error("Could not load image. Make sure it's a direct image link.")
else:
    uploaded_file = st.sidebar.file_uploader("Choose a Cadiz Photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")

if image:
    # State persistence for panels and master positioning
    if 'panels' not in st.session_state:
        st.session_state.panels = []
    if 'master_x' not in st.session_state:
        st.session_state.master_x = int(image.width * 0.1)
    if 'master_y' not in st.session_state:
        st.session_state.master_y = int(image.height * 0.1)

    # --- SIDEBAR: CONTROLS ---
    st.sidebar.header("1. Printer Settings")
    printer = st.sidebar.selectbox("Select Printer (Bleed/Wrap)", 
                                   ["Generic / Printify (0\")", 
                                    "CanvasChamp (1.5\" Wrap)", 
                                    "Walmart Photo (0.75\" Wrap)"])
    
    # Set bleed based on selection
    bleed = 1.5 if "CanvasChamp" in printer else (0.75 if "Walmart" in printer else 0.0)
    
    st.sidebar.header("2. Add Canvas Panel")
    new_w = st.sidebar.number_input("Panel Width (Inches)", value=12)
    new_h = st.sidebar.number_input("Panel Height (Inches)", value=12)
    
    if st.sidebar.button("➕ Add to Layout"):
        st.session_state.panels.append({'w': new_w, 'h': new_h, 'rel_x': 0, 'rel_y': 0})

    if st.sidebar.button("🗑️ Reset Everything"):
        st.session_state.panels = []
        st.rerun()

    # --- MASTER CONTROLS ---
    st.subheader("Master Movement (Move ALL Panels)")
    m_col1, m_col2 = st.columns(2)
    st.session_state.master_x = m_col1.slider("Horizontal Shift", 0, image.width, st.session_state.master_x)
    st.session_state.master_y = m_col2.slider("Vertical Shift", 0, image.height, st.session_state.master_y)

    # --- PANEL LIST & INDIVIDUAL OFFSET ---
    col_preview, col_panels = st.columns([3, 1])

    with col_panels:
        st.subheader("Fine-Tune Panels")
        for i, p in enumerate(st.session_state.panels):
            with st.expander(f"Panel {i+1} ({p['w']}x{p['h']})", expanded=False):
                p['rel_x'] = st.number_input(f"X Offset (P{i+1})", value=p['rel_x'], key=f"rx{i}")
                p['rel_y'] = st.number_input(f"Y Offset (P{i+1})", value=p['rel_y'], key=f"ry{i}")
                if st.button(f"Remove P{i+1}", key=f"del{i}"):
                    st.session_state.panels.pop(i)
                    st.rerun()

    # --- PREVIEW RENDER ---
    with col_preview:
        preview_dpi = 100 # Low res for faster browser viewing
        preview_img = image.copy()
        draw = ImageDraw.Draw(preview_img, "RGBA")

        for i, p in enumerate(st.session_state.panels):
            # Calc position: Master + Relative Offset
            final_x = st.session_state.master_x + p['rel_x']
            final_y = st.session_state.master_y + p['rel_y']
            pw, ph = int(p['w'] * preview_dpi), int(p['h'] * preview_dpi)

            # Draw Face (Cyan)
            draw.rectangle([final_x, final_y, final_x + pw, final_y + ph], outline="cyan", width=15)
            
            # Draw Wrap Area (Red)
            if bleed > 0:
                b_px = int(bleed * preview_dpi)
                draw.rectangle([final_x - b_px, final_y - b_px, final_x + pw + b_px, final_y + ph + b_px], 
                               outline="red", width=5)
            
            draw.text((final_x + 10, final_y + 10), f"P{i+1}", fill="white")

        st.image(preview_img, caption="Cyan = Front Face | Red = Side Wrap", use_container_width=True)

    # --- EXPORT ---
    st.divider()
    export_dpi = st.select_slider("Export Resolution (DPI)", options=[72, 150, 300], value=150)
    
    if st.button(f"🚀 PREPARE {len(st.session_state.panels)} FILES FOR {printer.upper()}"):
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, p in enumerate(st.session_state.panels):
                # High-res math
                fx = st.session_state.master_x + p['rel_x']
                fy = st.session_state.master_y + p['rel_y']
                
                # Apply bleed
                b_px = int(bleed * export_dpi)
                left = fx - b_px
                top = fy - b_px
                right = fx + int(p['w'] * export_dpi) + b_px
                bottom = fy + int(p['h'] * export_dpi) + b_px
                
                # Safeguard crop
                left, top = max(0, left), max(0, top)
                right, bottom = min(image.width, right), min(image.height, bottom)
                
                crop = image.crop((left, top, right, bottom))
                
                # Walmart Limit (8000px)
                if "Walmart" in printer and (crop.width > 8000 or crop.height > 8000):
                    crop.thumbnail((8000, 8000), Image.Resampling.LANCZOS)

                img_buf = BytesIO()
                crop.save(img_buf, format="JPEG", quality=95)
                zip_file.writestr(f"Panel_{i+1}_{p['w']}x{p['h']}.jpg", img_buf.getvalue())
        
        st.download_button(
            label="✅ DOWNLOAD PRODUCTION ZIP",
            data=zip_buf.getvalue(),
            file_name=f"farmhouse_frames_export.zip",
            mime="application/zip"
        )
