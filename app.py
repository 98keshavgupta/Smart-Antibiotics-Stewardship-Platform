import streamlit as st
import requests
import pandas as pd
import os

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="Smart Antibiotics Stewardship", layout="wide")
st.title("🏥 Smart Antibiotics Stewardship Platform")
st.markdown("*Universal Disease & Location Support*")

if 'disease_data' not in st.session_state:
    st.session_state.disease_data = {}
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = None
if 'step1_done' not in st.session_state:
    st.session_state.step1_done = False

# SECTION 1
st.subheader("Infection Details")
col1, col2 = st.columns(2)
with col1:
    disease = st.text_input("Disease (e.g., UTI, Pneumonia)", key="disease_input")
    mo = st.text_input("Microorganism (e.g., E. Coli, S. Pneumoniae)", key="mo_input")
with col2:
    location = st.text_input("Location (e.g., Guntur, Delhi)", key="location_input")

if st.button("Proceed (Fetch Data)"):
    if disease and location:
        st.session_state.disease_data = {"disease": disease, "microorganism": mo, "location": location}
        
        with st.spinner("🌐 Searching Local Antibiograms & Global Guidelines..."):
            try:
                resp = requests.post(f"{API_URL}/api/step1_search", json=st.session_state.disease_data, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    st.success("✅ Data Loaded!")
                    
                    if data['external_research']['results']:
                        with st.expander("📚 Live Research & Guidelines"):
                            for item in data['external_research']['results']:
                                st.markdown(f"- **{item['source']}**: [{item['title']}]({item['link']})")
                    
                    if data['local_sensitivity']:
                        st.info(f"📍 Found Local Antibiogram Data for {location}")
                    else:
                        st.warning(f"⚠️ No Local Data for {location}. Using Global Guidelines.")
                        
                    st.session_state.step1_done = True
                else:
                    st.error(f"Backend Error: {resp.status_code}")
            except Exception as e:
                st.error(f"Connection Failed: {e}. Ensure Backend is running on port 8000.")
    else:
        st.warning("Please fill Disease and Location.")

st.divider()

# SECTION 2
st.subheader("Patient Details")
if st.session_state.step1_done:
    c1, c2, c3 = st.columns(3)
    with c1:
        age = st.number_input("Age", min_value=0, max_value=120, value=30, key="age_input")
        crcl = st.number_input("CrCl (mL/min)", value=None, placeholder="Optional", key="crcl_input")
    with c2:
        sex = st.selectbox("Sex", ["Male", "Female", "Other"], key="sex_selector")
        allergy = st.text_input("Allergy (e.g., Penicillin)", placeholder="Optional", key="allergy_input")
        lfts = st.text_input("LFTs Status", placeholder="Optional", key="lfts_input")
    with c1:
        current_sex = st.session_state.get("sex_selector", "Male")
        disable_pregnancy = (current_sex != "Female")
        pregnancy = st.checkbox("Pregnant?", disabled=disable_pregnancy, key="pregnancy_checkbox")

    if st.button("Proceed (Generate Prescription)"):
        with st.spinner("🧠 Analyzing PK/PD & Guidelines..."):
            try:
                payload = {
                    **st.session_state.disease_data,
                    "age": age,
                    "sex": sex,
                    "pregnancy": pregnancy,
                    "allergy": allergy,
                    "crcl": crcl,
                    "lfts": lfts
                }
                resp = requests.post(f"{API_URL}/api/step2_recommend", json=payload, timeout=10)
                
                if resp.status_code == 200:
                    st.session_state.recommendations = resp.json()
                    st.success("✅ Prescription Generated!")
                else:
                    st.error(f"Error: {resp.status_code} - {resp.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
else:
    st.info("👈 Please complete Step 1 first.")

st.divider()

# SECTION 3
if st.session_state.recommendations:
    rec = st.session_state.recommendations.get('primary_recommendation', {})
    others = st.session_state.recommendations.get('other_options', [])
    
    st.subheader(" Final Recommendation")
    
    if rec:
        st.markdown(f"""
        <div style="background-color:#000000; padding:25px; border-left: 8px solid #00ff00; border-radius:10px; box-shadow: 0 4px 8px rgba(255,255,255,0.2);">
            <h2 style="margin-top:0; color:#ffffff; font-size:28px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">✅ Recommended: {rec.get('recommended', 'N/A')}</h2>
            <p style="font-size:18px; margin:8px 0; color:#ffffff;"><strong>💊 Dose:</strong> {rec.get('dose', 'N/A')}</p>
            <p style="font-size:18px; margin:8px 0; color:#ffffff;"><strong>📊 Sensitivity:</strong> {rec.get('sensitivity', 'N/A')}</p>
            <p style="font-size:18px; margin:8px 0; color:#ffffff;"><strong>🌍 AWaRe Category:</strong> {rec.get('aware', 'N/A')}</p>
            <p style="font-size:18px; margin:8px 0; color:#ffffff;"><strong>📝 Rationale:</strong> {rec.get('rationale', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

    if others:
        st.write("### 💊 Alternative Options")
        df = pd.DataFrame(others)
        if not df.empty:
            df_display = df[['drug_name', 'aware', 'sensitivity', 'rationale']]
            df_display.columns = ['Drug Name', 'AWaRe', 'Sensitivity', 'Rationale']
            st.dataframe(df_display, use_container_width=True)

    col_a, col_b, _ = st.columns([1, 1, 4])
    with col_a:
        if st.button("💾 Save Info"):
            if rec:
                save_payload = {
                    **st.session_state.disease_data,
                    "age": st.session_state.get("age_input", 30),
                    "sex": st.session_state.get("sex_selector", "Male"),
                    "pregnancy": st.session_state.get("pregnancy_checkbox", False),
                    "allergy": st.session_state.get("allergy_input", ""),
                    "crcl": st.session_state.get("crcl_input", None),
                    "lfts": st.session_state.get("lfts_input", ""),
                    "recommended_drug": rec.get('recommended', ''),
                    "dose": rec.get('dose', ''),
                    "sensitivity": rec.get('sensitivity', ''),
                    "aware": rec.get('aware', ''),
                    "rationale": rec.get('rationale', '')
                }
                try:
                    resp = requests.post(f"{API_URL}/api/save_patient", json=save_payload, timeout=10)
                    if resp.status_code == 200:
                        st.success("Patient data saved successfully!")
                    else:
                        st.error("Failed to save data.")
                except Exception as e:
                    st.error(f"Save error: {e}")

    with col_b:
        if st.button("🔄 Start New"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.query_params.clear()
            st.rerun()