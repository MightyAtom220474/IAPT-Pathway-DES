import streamlit as st
#from app_style import global_page_style


st.logo("https://lancsvp.org.uk/wp-content/uploads/2021/08/nhs-logo-300x189.png")

# with open("style.css") as css:
#     st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

#global_page_style('static/css/style.css')

st.subheader("Talking Therapies Pathway Simulation")

st.markdown(
    """
    ### NHS Talking Therapies Simulation

    This simulation models the journey of patients through the NHS Talking Therapies 
    service, focusing on the assessment and treatment pathway. It is built using 
    **SimPy**, a discrete-event simulation framework in Python that mimics real-world 
    processes over time — such as queues, waiting times, and limited resources like 
    therapists.

    The simulation starts when a patient is referred to the service. Each simulated 
    patient progresses through key stages: initial assessment, allocation to a 
    treatment type (e.g., low-intensity support like Psychological Wellbeing 
    Practitioner (PWP) sessions, or high-intensity therapy such as CBT or counselling), 
    and then treatment itself. At every stage, the model takes into account the 
    availability of staff, the number of other patients waiting, and specific rules 
    about how patients are prioritised or routed.

    This allows the simulation to capture the **dynamics and constraints of the real 
    service** — for example, how long people wait for assessments or treatment, how 
    backlogs form, and what impact staffing levels have on these delays. It also 
    supports experimentation: by changing parameters like referral rates or the number 
    of available therapists, we can explore “what if?” scenarios and see how the 
    system would respond.

    By running the simulation many times (with slightly different random inputs each 
    time), we get a robust picture of typical outcomes and variability — such as 
    average waiting times or treatment throughput. This kind of simulation helps 
    service planners and decision-makers understand bottlenecks, test ideas before 
    implementing changes, and ultimately improve the efficiency and responsiveness of 
    mental health services.
    """
)

st.write("Head to the 'Run Pathway Simulation' page to get started.")