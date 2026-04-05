import streamlit as st
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import zipfile

st.set_page_config(page_title="Farmhouse Frames Splitter", layout="wide")

st.title("🖼️ Farmhouse Frames: Professional Splitter")
st.write("Upload a Cadiz photo or use a URL to create custom-sized splits for CanvasChamp.")

# 1. Image Loading
img_source = st.sidebar.radio("Image Source", ["Upload Local File", "URL"])
image = None

if img_source == "URL":
    url = st.sidebar.text_input("Paste Image URL")
    if url:
        try:
            response = requests.get(url)
            image = Image.open(BytesIO(response.content)).convert("RGB")
        except:
            st.error("Could not load image. Check the URL.")
else:
    uploaded_file = st.sidebar.file_uploader("Choose a photo", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        image = Image.open(uploaded_file).convert("RGB")

if image:
    # Set up session state for panels
    if 'panels' not in st.session_state:
        st.session_state.panels = []

    # Sidebar: Add Panels
    st.sidebar.header("Add Canvas Size")
    w_in = st.sidebar.number_input("Width (Inches)", value=12)
    h_in = st.sidebar.number_input("Height (Inches)", value=24)
    dpi = st.sidebar.slider("DPI Setting (300 is standard for print)", 72, 300, 150)
    
    if st.sidebar.button("➕ Add This Panel"):
        st.session_state.panels.append({'w': w_in, 'h': h_in, 'x': 0, 'y': 0})

    if st.sidebar.button("🗑️ Reset All"):
        st.session_state.panels = []
        st.rerun()

    # Main Area: Positioning
    st.subheader("Position Your Panels")
    for i, p in enumerate(st.session_state.panels):
        with st.expander(f"Panel {i+1}: {p['w']}\"x{p['h']}\"", expanded=True):
            col_x, col_y, col_del = st.columns([3, 3, 1])
            p['x'] = col_x.slider(f"Left/Right", 0, image.width, p['x'], key=f"x{i}")
            p['y'] = col_y.slider(f"Up/Down", 0, image.height, p['y'], key=f"y{i}")
            if col_del.button("Remove", key=f"del{i}"):
                st.session_state.panels.pop(i)
                st.rerun()

    # Preview Rendering
    preview = image.copy()
    draw = ImageDraw.Draw(preview, "RGBA")
    for i, p in enumerate(st.session_state.panels):
        # Convert inches to pixels based on chosen DPI
        pw, ph = int(p['w'] * dpi), int(p['h'] * dpi)
        rect = [p['x'], p['y'], p['x'] + pw, p['y'] + ph]
        draw.rectangle(rect, outline="cyan", width=int(image.width/100))
        draw.text((p['x']+20, p['y']+20), f"PANEL {i+1}", fill="white")

    st.image(preview, caption="Your Layout Mockup", use_container_width=True)

    # Export
    if st.button("📦 PREPARE FILES FOR PRINTIFY"):
        zip_buf = BytesIO()
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            for i, p in enumerate(st.session_state.panels):
                pw, ph = int(p['w'] * dpi), int(p['h'] * dpi)
                crop = image.crop((p['x'], p['y'], p['x'] + pw, p['y'] + ph))
                img_buf = BytesIO()
                crop.save(img_buf, format="JPEG", quality=95)
                zip_file.writestr(f"panel_{i+1}_{p['w']}x{p['h']}.jpg", img_buf.getvalue())
        
        st.download_button(
            label="Download ZIP of all JPGs",
            data=zip_buf.getvalue(),
            file_name="farmhouse_frames_export.zip",
            mime="application/zip"
        )
