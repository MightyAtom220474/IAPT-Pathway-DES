import streamlit as st
#from app_style import global_page_style


st.logo("https://lancsvp.org.uk/wp-content/uploads/2021/08/nhs-logo-300x189.png")

# with open("style.css") as css:
#     st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

#global_page_style('static/css/style.css')

st.title("Talking Therapies Pathway Simulation")

st.write("Welcome to the Talking Therapies pathway simulation app! This " 
         "simulation is designed to model the flow of patients through the "
         "full Talking Therapies Assessment and Treatment Pathway")

st.write("Head to the 'Run Pathway Simulation' page to get started.")