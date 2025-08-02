import streamlit as st
import requests



st.set_page_config(page_title="Drug Interaction & Dosage Checker")
st.title("💊 Drug Interaction & Dosage Checker")

prescription = st.text_area("Enter Prescription Text")
age = st.number_input("Patient Age", min_value=0, max_value=120, value=25)
temperature = st.number_input("Body Temperature (°C)", min_value=30.0, max_value=45.0, value=37.0)

if st.button("Analyze Prescription"):
    payload = {
        "text": prescription,
        "age": age,
        "temperature": temperature
    }

    with st.spinner("Analyzing with Gemini AI..."):
        res = requests.post("https://medicalprescription.onrender.com/analyze", json=payload)
        if res.status_code == 200:
            data = res.json()
            st.subheader("🧬 Extracted Drugs")
            st.write(data["extracted_drugs"])

            st.subheader("⚠️ Interactions Found")
            if data["interactions"]:
                for i in data["interactions"]:
                    st.error(i)
            else:
                st.success("No known interactions found.")

            st.subheader("📋 Gemini's Recommendations")
            st.write(data["gemini_analysis"])
        else:
            st.error("Something went wrong while contacting the backend.")
