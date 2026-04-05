import streamlit as st
from PIL import Image, ImageDraw
import requests
from io import BytesIO
import zipfile
from streamlit_cropper import st_cropper

st.set_page_config(page_title="Farmhouse Frames - Layout Builder", layout="wide")

st.title("🖼️ Farmhouse Frames: Frame-First Designer")
st.write("1. Define your canvas sizes | 2. Position your photo within the layout.")

# --- STEP 1: DEFINE THE LAYOUT ---
st.sidebar.header("1. Build Your Layout")
printer = st.sidebar.selectbox("Printer (Bleed)", ["Generic (0\")", "CanvasChamp (1.5\")", "Walmart (0.75\")"])
bleed = 1.5 if "CanvasChamp" in printer else (0.75 if "Walmart" in printer else 0.0)

if 'layout_panels' not in st.session_state:
    st.session_state.layout_panels = []

col_w, col_h = st.sidebar.columns(2)
new_w = col_w.number_input("Width (in)", value=12)
new_h = col_h.number_input("Height (in)", value=24)

if st.sidebar.button("➕ Add Canvas to Layout"):
    st.session_state.layout_panels.append({'w': new_w, 'h': new_h})

if st.sidebar.button("🗑️ Clear Layout"):
    st.session_state.layout_panels = []
    st.rerun()

# Display current layout summary
if st.session_state.layout_panels:
    st.sidebar.write("### Current Layout")
    total_w = sum(p['w'] for p in st.session_state.layout_panels)
    max_h = max(p['h'] for p in st.session_state.layout_panels)
    st.sidebar.info(f"Total Span: {total_w}\" x {max_h}\"")
else:
    st.info("Add your canvas sizes in the sidebar to begin.")
    st.stop()

# --- STEP 2: UPLOAD PHOTOGRAPHY ---
st.sidebar.header("2. Upload Photography")
img_file = st.sidebar.file_uploader("Upload your Cadiz Photo", type=["jpg", "png", "jpeg"])

if img_file:
    img = Image.open(img_file).convert("RGB")
    
    # Calculate target aspect ratio of the ENTIRE layout
    target_aspect = total_w / max_h
    
    st.subheader("3. Drag & Position Photo Within Frames")
    st.write("The box below represents your total wall art span. Drag it to find the best composition.")

    # The Cropper tool will force the aspect ratio of your combined canvases
    rect = st_cropper(img, realtime_update=True, box_color='#00FFFF', aspect_ratio=(total_w, max_h))
    
    # --- STEP 3: SPLIT & EXPORT ---
    if st.button("🚀 PREPARE INDIVIDUAL PRODUCTION FILES"):
        zip_buf = BytesIO()
        
        # 'rect' is the cropped "master" image of the whole layout
        # We now slice 'rect' into the individual panel widths
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
            current_x = 0
            for i, p in enumerate(st.session_state.layout_panels):
                # Calculate what percentage of the total width this panel takes
                panel_width_pct = p['w'] / total_w
                px_width = int(rect.width * panel_width_pct)
                
                # Crop the specific panel out of the master crop
                panel_crop = rect.crop((current_x, 0, current_x + px_width, rect.height))
                
                # Handle resizing to target height (if panels are different heights)
                # This ensures the "Face" matches your requested inches
                if p['h'] < max_h:
                    # Logic for panels that are shorter than the layout max (centered vertically)
                    h_diff = rect.height - int(rect.height * (p['h']/max_h))
                    panel_crop = panel_crop.crop((0, h_diff//2, panel_crop.width, panel_crop.height - h_diff//2))

                # Add Bleed (Wrap) if selected
                if bleed > 0:
                    # We add a colored border or expanded crop here 
                    # For production, we simply tag the file for the printer
                    pass 

                # Save to ZIP
                img_buf = BytesIO()
                panel_crop.save(img_buf, format="JPEG", quality=95)
                zip_file.writestr(f"Panel_{i+1}_{p['w']}x{p['h']}.jpg", img_buf.getvalue())
                
                current_x += px_width
        
        st.success("Splits generated successfully!")
        st.download_button("Download ZIP for Walmart/CanvasChamp", zip_buf.getvalue(), "farmhouse_production.zip")
