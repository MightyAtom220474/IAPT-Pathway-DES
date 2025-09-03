import simpy
import random
import numpy as np
import pandas as pd
import streamlit as st
#import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from iapt_classes import g, Trial, load_referral_rates, load_base_params
#from app_style import global_page_style

########## Streamlit App ##########

st.set_page_config(layout="wide")

#@st.cache_data

# def load_referral_rates():  # Thanks to Sammi Rosser :-)
#     return pd.read_csv(
#         ("https://raw.githubusercontent.com/MightyAtom220474/IAPT-Pathway-DES/"
#          "refs/heads/main/.streamlit/talking_therapies_referral_rates.csv"),
#         index_col=0)


#st.logo("https://lancsvp.org.uk/wp-content/uploads/2021/08/nhs-logo-300x189.png")

# Import custom css for using a Google font
# with open("style.css") as css:
#    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

#global_page_style('static/css/style.css')

base_params_df = load_base_params()

print(base_params_df)

team_list = base_params_df.iloc[:, 0].tolist()

print(team_list)

st.subheader("Talking Therapies Pathway Simulation")

with st.sidebar:

    st.subheader("Team Selection")

    team_select_input = st.multiselect('Please select a team to configure the '\
                    'model or leave blank for default settings',
                   options=team_list,help='Please select a team. This will set'\
                   ' the base parameters for that team such as number of ' \
                    'referrals, rejection rates, DNA rates etc.'
                   ,max_selections=1,default=None)

    st.subheader("Model Inputs")

    with st.expander("Screening & Assessment"):

        # Referral Inputs
        st.markdown("#### Screening")
        referral_input = st.slider("Average Number of Referrals Per Week", 0, 1500
                                   ,65,help='The mean number of referrals '
                                  'received per week. This will be used as the '
                                  'basis for seasonal variations based on '
                                  'historical referral data')
        prevalence_input = st.slider("Expected Prevalence", 0, 500
                                   , 220,help='The expected Prevalence level '
                                   'for this team or service')
        ta_wl_input = st.number_input("Current Telephone Assessment Waiting List",
                                    min_value=0, max_value=1000, step=1,
                                    value=200,help='The current number of '
                                        'patients on the assessment waiting '
                                        'list, default is 0')
        if ta_wl_input > 0:
            ta_wait_input = st.number_input("Current Average TA Waiting Time (weeks)",
                                           min_value=0, max_value=52, step=1,
                                           value=3,help='If a waiting list value '
                                           'has been entered above, the average '
                                           'waiting time in weeks for patients '
                                           'on the TA waiting list')
        else:
            ta_wait_input = 0
        referral_reject_input = st.number_input("Referral Rejection Rate (%)",
                        min_value=0.0, max_value=20.0, step=0.25, value=4.25,
                        help='The % of referrals that get rejected on initial '
                        'referral, prior to any screening process e.g. due to '
                        'missing information, inappropriate for service etc.')
        referral_review_input = st.number_input("% of Referrals Sent for Screening",
                        min_value=0.0, max_value=100.0, step=0.5, value=60.0,
                        help='The % of referrals that get sent for further '
                        'screening')
        referral_reject_input = st.number_input("Screening Rejection Rate (%)",
                        min_value=0.0, max_value=100.0, step=0.25, 
                        value=g.review_rej_rate*100,help='The % of referrals '
                        'that get rejected as a result of the screening process')
        referral_screen_input = st.slider("Number of Mins to Screen Referral",
                                          1, 30, 20,help='Taken from Job '
                                            'Plans: the number of minutes allocated '
                                            'for a Referral to be screened')
        opt_in_input = st.number_input("% of Referrals that Opt-in",
                        min_value=50.0, max_value=100.0, step=0.5, value=75.0,
                        help='The % of referrals that opt-in to treatment')
        st.markdown("#### Assessment")
        ta_resource_pwp = st.slider("Number of TA Slots per PwP per Week"
                                    , 0, 15, 9,help='Taken from Job '
                                            'Plans: the number of TA slots that '
                                            'each PwP is expected to offer per '
                                            'week. This serves as a resource '
                                            'to decide whether a patient is '
                                            'assessed or if all available '
                                            'resources that week have been used, '
                                            'is added to the assessment '
                                            'waiting list')
        ta_accept_input = st.number_input("% of TA's that are Accepted",
                        min_value=50.0, max_value=100.0, step=0.5, value=70.0)
        ta_time_input = st.slider("Number of Mins to Perform TA", 1, 90, 60
                                  ,help='Taken from Job Plans: the number of '
                                            'minutes allocated for a patient to '
                                            'be assessed')
        step2_step3_rate_input = st.number_input(
                                "% of Patients Assigned to Step 2 vs Step 3",
                        min_value=0.0, max_value=100.0, step=0.5, value=47.0
                        ,help='The percentage of patients that get allocated to '
                        'Step 2 versus Step 3 e.g. a value of 47.0 '
                        'will send 47% of patients down the Step 2 route and '
                        '53% down the Step 3 route')
           
    with st.expander("Step 2"):
        
        # Triage Inputs
        st.divider()
        st.markdown("#### Step 2")
        
        step2_path_ratio = st.number_input("% of Step 2 Allocated to PwP vs Group",
                                           min_value=0.0, max_value=100.0, 
                                           step=1.0, value=47.0,help='The percentage '
                                          'of patients that get allocated to '
                                          '1:1 versus Groups e.g. a value of 47.0 '
                                          'will send 47% of patients down the '
                                          '1:1 path and 53% down the Group path')
        pwp_wl_input = st.number_input("Current PwP 1:1 Waiting List", 
                                      min_value=0, max_value=1000, step=1,
                                      value=74,help='The current number of '
                                        'patients on the PwP 1:1 waiting '
                                        'list, default is 0')
        if pwp_wl_input > 0:
            pwp_wait_input = st.number_input("Current Average PwP 1:1 Waiting Time (weeks)",
                                            min_value=0, max_value=52, step=1,
                                            value=2,help='If a waiting list value '
                                           'has been entered above, the average '
                                           'waiting time in weeks for patients '
                                           'on the PwP 1:1 waiting list')
        else:
            pwp_wait_input = 0
        step2_first_input = st.slider("Number of Mins for First PwP Appointment",
                                            1, 60, 45,help='Taken from Job '
                                            'Plans: the number of minutes allocated '
                                            'for a Step 2 First appointment')
        step2_fup_input = st.slider("Number of Mins for Follow-up PwP Appointment",
                                    1, 60, 30,help='Taken from Job Plans: '
                                            'the number of minutes allocated '
                                            'for a Step 2 Follow-up appointment')
        step2_admin_input = st.slider("Number of Mins for Writing up Step2 Appointment",
                                    1, 20, 15,help='Taken from Job Plans: '
                                    'The number of minutes allocated for '
                                    'administrative tasks, writing up etc. '
                                    'following a Step 2 appointment')
        step_up_input = st.number_input("% of Patients Stepped Up", 
                                        min_value=0.0, max_value=10.0,
                                        step=0.25, value=1.0,help='The percentage'
                                          ' of patients that get stepped up'
                                          ' onto the Step 3 pathway as they '
                                          'approach then end of their Step 2 '
                                          'treatment')
        step2_pwp_dna_input = st.number_input("% DNA's for PwP Appointments",
                                            min_value=0.0, max_value=30.0,
                                            step=0.5, value=15.0,help='The % of '
                                            'PwP 1:1 appointments where the '
                                            'patient Did Not Attend')
        step2_group_dna_input = st.number_input("% DNA's for Group Sessions",
                                               min_value=0.0, max_value=30.0,
                                               step=0.25, value=22.0,help='The % of '
                                               'Group appointments where the '
                                               'patient Did Not Attend')
        step2_group_sessions_input = st.slider("Number of Step2 Group Sessions",
                                              1, 10, 7,help='The number of '
                                              'sessions typically offered for '
                                              'PwP Group Therapy')
        step2_group_size_input = st.slider("Maximum Step2 Group Size", 1, 12, 7,
                                           help='The maximum number of '
                                           'attendees on a course of Step 2 '
                                           'Group Therapy')
        step2_group_duration_input = st.number_input("Length of Group Sessions (mins)",
                                                min_value=180, max_value=300,
                                                step=30, value=240,help='The '
                                                'standard duration in minutes '
                                                'of a Step 2 Group Therapy ' \
                                                'session')

    with st.expander("Step 3"):
        
        # Triage Inputs
        st.divider()
        st.markdown("#### Step 3")
        
        step3_path_ratio = st.number_input("% of Step 3 Allocated to DepC vs CBT",
                                           min_value=0.0, max_value=100.0,
                                           step=0.5, value=37.0,help='The percentage '
                                          'of patients that get allocated to '
                                          'CBT versus DepC e.g. a value of 37.0 '
                                          'will send 37% of patients down the '
                                          'CBT path and 63% down the DepC path')
        step_down_input = st.number_input("% of Patients Stepped Down",
                                          min_value=0.0, max_value=20.0,
                                          step=0.5, value=12.0,help='The percentage '
                                          'of patients that get stepped down '
                                          'onto the Step 2 pathway as they '
                                          'approach then end of their Step 3 '
                                          'treatment')
        cbt_wl_input = st.number_input("Current CBT Waiting List", min_value=0, 
                                    max_value=1000, step=1, value=130,
                                    help='The current number of patients on the '
                                    'CBT waiting list, default is 0')
        if cbt_wl_input > 0:
            cbt_wait_input = st.number_input("Current Average CBT Waiting Time"
                                             " (weeks)", min_value=0, 
                                             max_value=52, step=1, value=5,
                                             help='If a waiting list value has '
                                             'been entered above, the average '
                                             'waiting time in weeks for patients '
                                             'on the CBT waiting list')
        else:
            cbt_wait_input = 0
        step3_cbt_first_input = st.slider("Number of Mins for First CBT Appointment",
                                          1, 180, 90,help='Taken from Job '
                                            'Plans: the number of minutes allocated '
                                            'for a CBT First appointment')
        step3_cbt_fup_input = st.slider("Number of Mins for Follow-up CBT Appointment",
                                        1, 90, 60,help='Taken from Job '
                                            'Plans: the number of minutes allocated '
                                            'for a CBT Follow-up appointment')
        step3_cbt_dna_input = st.number_input("% DNA's for CBT Appointments",
                                              min_value=0.0, max_value=30.0,
                                              step=0.5, value=20.0)
        couns_wl_input = st.number_input("Current DepC Waiting List",
                                        min_value=0, max_value=1000,
                                        step=1, value=250,help='The current '
                                        'number of patients on the '
                                        'DepC waiting list, default is 0')
        if couns_wl_input > 0:
            couns_wait_input = st.number_input("Current Average DepC Waiting "
                                               "Time (weeks)", min_value=0,
                                               max_value=52, step=1, value=10,
                                               help='If a waiting list value has '
                                            'been entered above, the average '
                                             'waiting time in weeks for patients '
                                             'on the DepC waiting list')
        else:
            couns_wait_input = 0
        step3_couns_first_input = st.slider("Number of Mins for First DepC Appointment",
                                            1, 180, 90,help='Taken from Job '
                                            'Plans: the number of minutes allocated '
                                            'for a DepC First appointment')
        step3_couns_fup_input = st.slider("Number of Mins for Follow-up DepC Appointment",
                                          1, 90, 60,help='Taken from Job '
                                            'Plans: the number of minutes allocated '
                                            'for a DepC Follow-up appointment')
        step3_admin_input = st.slider("Number of Mins for Writing up Step3 Appointment",
                                    1, 20, 15,help='Taken from Job '
                                            'Plans: the number of minutes allocated '
                                            'for admin and writing up following '
                                            'a Step 3 appointment')
        step3_couns_dna_input = st.number_input("% DNA's for DepC Sessions",
                                                min_value=0.0, max_value=30.0,
                                                step=0.25, value=20.0)
        step3_session_var_input = st.number_input(
                    "% of Instances where Patients Receive Additional Sessions",
                                                  min_value=0.0, max_value=30.0,
                                                  step=0.25, value=20.0,
                                                  help='The % of instances '
                                                  'where a patient receives '
                                                  'additional treatment '
                                                  'sessions over and above '
                                                  'the standard for that mode '
                                                  'of treatment. Uses an '
                                                  'exponential distribution '
                                                  'with upper and lower limits '
                                                  'based on data supplied by '
                                                  'the service to determine '
                                                  'how many additional sessions '
                                                  'a patient receives')
        
        delayed_disch_input = st.number_input(
                    "% of Instances where Patients Discharge is Delayed",
                                                  min_value=0.0, max_value=30.0,
                                                  step=0.5, value=10.0,
                                                  help='The % of patients where '
                                            'they are not removed from the '
                                            'caseload immediately upon '
                                            'completion of treatment. Uses an '
                                            'exponential distribution with a '
                                            'lower limit of 1 week and an '
                                            'upper limit of 13 weeks')
        
        # code for conditional streamlit inputs
        # if triage_wl_input > 0:
        #     triage_wait_input = st.number_input("Current Average Triage Waiting Time (weeks)", min_value=0, max_value=52, step=1, value=0)
        # else:
        #     triage_wait_input = 0
    
    with st.expander("Job Plans"):

        st.divider()
        st.markdown("#### Job Plans")
        cbt_avail_input = st.number_input(label="Starting Number of CBT Practitioners WTE",
                                          min_value=1,max_value=200,
                                          step=1,value = 7,help='The current '
                                            'number of CBT practitioners working '
                                            'within the team or service')
        couns_avail_input = st.number_input(label="Starting Number of DepC Practitioners WTE",
                                            min_value=1,max_value=100,
                                            step=1,value = 2,help='The current '
                                            'number of DepC practitioners working '
                                            'within the team or service')
        pwp_avail_input = st.number_input(label="Starting Number of PwP Practitioners WTE",
                                          min_value=1,max_value=200,
                                          step=1,value = 6,help='The current '
                                            'number of PwP practitioners working '
                                            'within the team or service')
        cbt_add_input = st.number_input("Change in Number of CBT Practitioners WTE",
                        min_value=-20, max_value=20, step=1, value=0,help='The '
                                            'potential change in the number of '
                                            'CBT practitioners within the team '
                                            'or service - can be +ve or -ve')
        couns_add_input = st.number_input("Change in Number of DepC Practitioners WTE",
                        min_value=-10, max_value=20, step=1, value=0,help='The '
                                            'potential change in the number of '
                                            'DepC practitioners within the team '
                                            'or service - can be +ve or -ve')
        pwp_add_input = st.number_input("Change in Number of PwP Practitioners WTE",
                        min_value=-25, max_value=25, step=1, value=0,help='The '
                                            'potential change in the number of '
                                            'PwP practitioners within the team '
                                            'or service - can be +ve or -ve')
        cbt_caseload_input = st.slider("Number of Patients Allowed on CBT Caseload",
                                            1, 50, g.cbt_caseload,help='The '
                                            'maximum number of patients '
                                            'allowed on a CBT practitioners '
                                            'caseload per WTE. Once this limit '
                                            'is reached patients will have to '
                                            'wait until a slot becomes available. '
                                            'Default is 100 so that availability '
                                            'of First appointments is used to '
                                            'decide whether to treat or add to '
                                            'waiting list')
        couns_caseload_input = st.slider("Number of Patients Allowed on DepC Caseload",
                                            1, 50, g.couns_caseload,help='The '
                                            'maximum number of patients '
                                            'allowed on a DepC practitioners '
                                            'caseload per WTE. Once this limit '
                                            'is reached patients will have to '
                                            'wait until a slot becomes available. '
                                            'Default is 100 so that availability '
                                            'of First appointments is used to '
                                            'decide whether to treat or add to '
                                            'waiting list')
        pwp_caseload_input = st.slider("Number of Patients Allowed on PwP Caseload",
                                            1, 100, g.pwp_caseload,help='The '
                                            'maximum number of patients '
                                            'allowed on a PwP practitioners '
                                            'caseload per WTE. Once this limit '
                                            'is reached patients will have to '
                                            'wait until a slot becomes available. '
                                            'Default is 100 so that availability '
                                            'of First appointments is used to '
                                            'decide whether to treat or add to '
                                            'waiting list')
        cbt_first_input = st.slider("Number of First Appointments per week per CBT Prac",
                                            1, 10, 2,help='The number of First '
                                            'appointments a CBT practitioner '
                                            'offers per week. This is used to '
                                            'decide whether a patient is added '
                                            'to the caseload or the waiting '
                                            'list. If an appointment is '
                                            'available they will be added to the '
                                            'caseload. If all First appointments '
                                            'have been used for that week they '
                                            'will be added to the waiting list')
        couns_first_input = st.slider("Number of First Appointments per week per Couns Prac",
                                            1, 10, 2,help='The number of First '
                                            'appointments a DepC practitioner '
                                            'offers per week. This is used to '
                                            'decide whether a patient is added '
                                            'to the caseload or the waiting '
                                            'list. If an appointment is '
                                            'available they will be added to the '
                                            'caseload. If all First appointments '
                                            'have been used for that week they '
                                            'will be added to the waiting list')
        pwp_first_input = st.slider("Number of First Appointments per week per PwP Prac",
                                            1, 10, 4,help='The number of First '
                                            'appointments a PwP practitioner '
                                            'offers per week. This is used to '
                                            'decide whether a patient is added '
                                            'to the caseload or the waiting '
                                            'list. If an appointment is '
                                            'available they will be added to the '
                                            'caseload. If all First appointments '
                                            'have been used for that week they '
                                            'will be added to the waiting list')
        cbt_hours_avail_input = st.number_input(label="Non-Clinical Hours p/w for CBT Pratitioners",
                                                min_value=10.0,max_value=25.0,
                                                step=0.5,
                                                value = g.hours_avail_cbt,
                                                help='Taken from Job Plans: '
                                                'The number of hours p/w a CBT '
                                                'practitioner allocates to '
                                                'non-clinical activity e.g. '
                                                'breaks, CPD, Wellbeing etc.')
        couns_hours_avail_input = st.number_input(label="Non-Clinical Hours p/w for DepC Pratitioners",
                                                  min_value=10.0,max_value=25.0,
                                                  step=0.5,
                                                  value = g.hours_avail_couns,
                                                  help='Taken from Job Plans: '
                                                'The number of hours p/w a DepC '
                                                'practitioner allocates to '
                                                'non-clinical activity e.g. '
                                                'breaks, CPD, Wellbeing etc.')
        pwp_hours_avail_input = st.number_input(label="Non-Clinical Hours p/w for PwP Pratitioners",
                                                min_value=10.0,max_value=25.0,
                                                step=0.5,
                                                value = g.hours_avail_pwp,
                                                help='Taken from Job Plans: '
                                                'The number of hours p/w a PwP '
                                                'practitioner allocates to '
                                                'non-clinical activity e.g. '
                                                'breaks, CPD, Wellbeing etc.')
        weeks_lost_input = st.number_input("Weeks Lost to Leave/Sickness etc.",
                            min_value=0.0, max_value=20.0, step=0.25, value=10.0,
                            help='The number of weeks of activity lost per '
                            'year to annual leave and sickness')
            
    with st.expander("Simulation Parameters"):
    
        st.divider()
        st.markdown("#### Simulation Parameters")
        sim_duration_input =  st.slider("Simulation Duration (weeks)",
                                        min_value=26, max_value=520,
                                        value=52, step=26,help='The number of '
                                        'weeks the simulation is being run for '
                                        'minimum 26 weeks, maximum 520 weeks '
                                        '(10 years)')
        st.write(f"The service is running for {sim_duration_input} weeks")
        number_of_runs_input = st.slider("Number of Simulation Runs", 1, 20, 2,
                                         help='The number of simulation runs '
                                         'refers to how many times you repeat '
                                         'the entire simulation process '
                                         'independently. Each run can produce '
                                         'different results due to randomness. ' 
                                         'Running the simulation multiple times '
                                         'allows you to capture variability in '
                                         'outcomes, estimate averages and '
                                         'confidence intervals, and ensure '
                                         'robustness of results. It is '
                                         'essential for statistical analysis '
                                         'and drawing reliable conclusions '
                                         'from the simulation')
        #st.toggle(label='Test Run?', value=False)

g.referral_rate_lookup = load_referral_rates()
g.prevalence = prevalence_input

##### Screening
g.mean_referrals_pw = referral_input
g.ta_waiting_list = ta_wl_input
g.ta_avg_wait = ta_wait_input
g.referral_rejection_rate = referral_reject_input/100
g.referral_review_rate = referral_review_input
g.referral_screen_time = referral_screen_input
g.opt_in_rate = opt_in_input/100
g.ta_accept_rate = ta_accept_input/100
g.step2_step3_ratio = (step2_step3_rate_input/100,1-(step2_step3_rate_input/100))

##### Step 2
g.step2_path_ratios = (step2_path_ratio/100,1-(step2_path_ratio/100))
g.pwp_waiting_list = pwp_wl_input
g.pwp_avg_wait = pwp_wait_input
g.step2_pwp_1st_mins = step2_first_input
g.step2_pwp_fup_mins = step2_fup_input
g.step2_pwp_dna_rate = step2_pwp_dna_input/100
g.step2_group_dna_rate = step2_group_dna_input/100
g.step2_group_sessions = step2_group_sessions_input
g.step2_group_size = step2_group_size_input
g.step2_group_session_mins = step2_group_duration_input
g.step_up_rate = step_up_input/100
g.step_up_rate = step_up_input/100
g.step2_session_admin = step2_admin_input

##### Step 3
g.step3_path_ratios = (step3_path_ratio/100,1-(step3_path_ratio/100))
g.cbt_waiting_list = cbt_wl_input
g.cbt_avg_wait = cbt_wait_input
g.step3_cbt_1st_mins = step3_cbt_first_input
g.step3_cbt_fup_mins = step3_cbt_fup_input
g.step3_cbt_dna_rate = step3_cbt_dna_input/100
g.couns_waiting_list = couns_wl_input
g.couns_avg_wait = couns_wait_input
g.step3_couns_1st_mins = step3_couns_first_input
g.step3_couns_fup_mins = step3_couns_fup_input
g.step3_couns_dna_rate = step3_couns_dna_input/100
g.step_down_rate = step_down_input/100
g.step3_session_admin = step3_admin_input
g.delayed_disc_var = delayed_disch_input

##### Job Plans
g.cbt_caseload = cbt_caseload_input
cbt_caseload_max = 35
g.couns_caseload = couns_caseload_input
couns_caseload_max = 35
g.pwp_caseload = pwp_caseload_input
pwp_caseload_max = 45
staff_weeks_lost = weeks_lost_input
weeks_lost_pc = (52-staff_weeks_lost)/52
total_cbt_hours = g.cbt_avail*37.5
total_couns_hours = g.couns_avail*37.5
total_pwp_hours = g.pwp_avail*37.5
clin_pwp_hours = g.pwp_avail*(pwp_hours_avail_input)
clin_cbt_hours = g.cbt_avail*(cbt_hours_avail_input)
clin_couns_hours = g.couns_avail*(couns_hours_avail_input)
staff_weeks_lost = weeks_lost_input
weeks_lost_pc = (52-staff_weeks_lost)/52 # turn number of weeks lost into a %
g.cbt_avail = int((cbt_avail_input + cbt_add_input)*weeks_lost_pc)
g.couns_avail = int((couns_avail_input + couns_add_input)*weeks_lost_pc)
g.pwp_avail = int((pwp_avail_input + pwp_add_input)*weeks_lost_pc)
g.pwp_1st_res = g.pwp_avail * pwp_first_input #  4 1st's per PwP per week
g.cbt_1st_res = g.cbt_avail * cbt_first_input #  2 1st's per CBT per week
g.couns_1st_res = g.couns_avail * couns_first_input # 2 1st's per Couns per week
g.ta_resource = g.pwp_avail * ta_resource_pwp #int(g.pwp_avail_tot*weeks_lost_pc)
g.sim_duration = sim_duration_input
g.number_of_runs = number_of_runs_input

###########################################################
# Run a trial using the parameters from the g class and   #
# print the results                                       #
###########################################################

#st.session_state.sim_data = {}

# Initialize sim_data in session_state if not already there
if "sim_data" not in st.session_state:
    st.session_state.sim_data = None

# Button to trigger simulation
button_run_pressed = st.button("Run simulation")

# Run the simulation only when button is pressed
if button_run_pressed:
    with st.spinner('Simulating the system...'):
        # Create environment and trial instance
        env = simpy.Environment()
        my_trial = Trial(env)
        pd.set_option('display.max_rows', 1000)

        # Run the simulation
        step2_results_df, step2_sessions_df, step3_results_df, step3_sessions_df, \
        asst_weekly_dfs, step2_waiting_dfs, step3_waiting_dfs, staff_weekly_dfs, \
        caseload_weekly_dfs = my_trial.run_trial()

        # Store results safely in session_state
        st.session_state.sim_data = {
            "step2_results_df": step2_results_df,
            "step2_sessions_df": step2_sessions_df,
            "step3_results_df": step3_results_df,
            "step3_sessions_df": step3_sessions_df,
            "asst_weekly_dfs": asst_weekly_dfs,
            "step2_waiting_dfs": step2_waiting_dfs,
            "step3_waiting_dfs": step3_waiting_dfs,
            "staff_weekly_dfs": staff_weekly_dfs,
            "caseload_weekly_dfs": caseload_weekly_dfs
        }

        # st.success("Simulation complete!")

# Only display outputs if simulation has run
# if st.session_state.sim_data:
#     st.subheader("Simulation Data Overview")
#     for name, df in st.session_state.sim_data.items():
#         st.write(f"**{name}**")
#         st.dataframe(df if isinstance(df, pd.DataFrame) else pd.concat(df, ignore_index=True))

        # st.subheader(f'Summary of all {g.number_of_runs} Simulation Runs over {g.sim_duration} Weeks')
        # st.subheader(f' Weeks with {cbt_add_input} change in CBT, {couns_add_input} change in DepC and ')
        # st.subheader(f'{pwp_add_input} change in PwP Practitioners')

        #st.write(step2_sessions_df)
        
        ##### get all data structured correctly for dashboard #####
        #st.write(asst_weekly_dfs)   
        asst_weekly_dfs['Referral Screen Hrs'] = asst_weekly_dfs['Referral Screen Mins']/60
        #asst_weekly_dfs['TA Hrs'] = asst_weekly_dfs['TA Mins']/60
        asst_weekly_dfs['Accepted Referrals'] = asst_weekly_dfs['Referrals Received'
                                                ]-asst_weekly_dfs['Referrals Rejected']
       
        # filter dataframe to just return columns needed
        asst_weekly_summary = asst_weekly_dfs[['Run Number','Week Number',
                                    'Referrals Received','Referral Screen Hrs',
                                    'Accepted Referrals','Referrals Rejected',
                                    'Referrals Reviewed','Reviews Rejected',
                                    'Referrals Opted-in','TA Waiting List',
                                    'TA 6W PC','Prev PC','TA Avg Wait',
                                    'TA Max Wait','TA Total Accept','TA Hrs'
                                    ]].reset_index()
        #st.write(asst_weekly_summary)       
        # asst_weekly_summary = asst_weekly_summary[asst_weekly_summary[
        #                     "Week Number"] != 0].reset_index(drop=True)
                              
        step2_pwp_results_summary = step2_results_df.loc[step2_results_df[
                'Route Name'] == 'pwp',['Run Number', 'Week Number', 
                                        'IsStep','IsDropout']].reset_index(drop=True)
        
        step2_pwp_waiting_summary = step2_waiting_dfs.loc[step2_waiting_dfs[
                'Route Name'] == 'pwp',['Run Number', 'Week Number', 
                                      'Num Waiting','Avg Wait','Max Wait'
                                      ,'Avg RTT','Max RTT']].reset_index(drop=True)
        
        #st.write(step2_pwp_waiting_summary)

        step2_pwp_sessions_summary = step2_sessions_df.loc[step2_sessions_df[
                'Route Name'] == 'pwp', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
        
        step2_pwp_session_type_summary = step2_sessions_df.loc[step2_sessions_df[
                'Route Name'] == 'pwp', ['Run Number', 'Week Number', 
                                      'Session Number','Session Type','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
               
        step2_group_results_summary = step2_results_df.loc[step2_results_df[
                'Route Name'] == 'group',['Run Number', 'Week Number', 
                                        'IsStep','IsDropout']].reset_index(drop=True)
        
        step2_group_waiting_summary = step2_waiting_dfs.loc[step2_waiting_dfs[
                'Route Name'] == 'group',['Run Number', 'Week Number', 
                                      'Num Waiting','Avg Wait','Max Wait'
                                      ,'Avg RTT','Max RTT']].reset_index(drop=True)
        
        step2_group_sessions_summary = step2_sessions_df.loc[step2_sessions_df[
                'Route Name'] == 'group', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
        
        #st.write(step2_group_sessions_summary)
        
        step2_group_session_type_summary = step2_sessions_df.loc[step2_sessions_df[
                'Route Name'] == 'group', ['Run Number', 'Week Number', 
                                      'Session Number','Session Type','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
        
        step3_cbt_results_summary = step3_results_df.loc[step3_results_df[
                'Route Name'] == 'cbt', ['Run Number', 'Week Number', 
                                      'IsStep','IsDropout']].reset_index(drop=True)
        
        step3_cbt_waiting_summary = step3_waiting_dfs.loc[step3_waiting_dfs[
                'Route Name'] == 'cbt',['Run Number', 'Week Number', 
                                      'Num Waiting','Avg Wait','Max Wait'
                                      ,'Avg RTT','Max RTT']].reset_index(drop=True)
        
        step3_cbt_sessions_summary = step3_sessions_df.loc[step3_sessions_df[
                'Route Name'] == 'cbt', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
        
        step3_cbt_session_type_summary = step3_sessions_df.loc[step3_sessions_df[
                'Route Name'] == 'cbt', ['Run Number', 'Week Number', 
                                      'Session Number','Session Type','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
        
        step3_couns_results_summary = step3_results_df.loc[step3_results_df[
                'Route Name'] == 'couns', ['Run Number', 'Week Number', 
                                      'WL Posn','Q Time',
                                      'IsStep','IsDropout']].reset_index(drop=True)
        
        step3_couns_waiting_summary = step3_waiting_dfs.loc[step3_waiting_dfs[
                'Route Name'] == 'couns',['Run Number', 'Week Number', 
                                      'Num Waiting','Avg Wait','Max Wait'
                                      ,'Avg RTT','Max RTT']].reset_index(drop=True)
        
        step3_couns_sessions_summary = step3_sessions_df.loc[step3_sessions_df[
                'Route Name'] == 'couns', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
        
        step3_couns_session_type_summary = step3_sessions_df.loc[step3_sessions_df[
                'Route Name'] == 'couns', ['Run Number', 'Week Number', 
                                      'Session Number','Session Type','Session Time',
                                      'Admin Time','IsDNA']].reset_index(drop=True)
        
        # Aggregation and renaming map
        agg_mapping = {
            'Session Number': 'count',
            'Session Time': 'sum',
            'Admin Time': 'sum',
            'IsDNA': 'sum'
        }
        rename_map = {
            'Session Number': 'Session_Count',
            'Session Time': 'Total_Session_Time',
            'Admin Time': 'Total_Admin_Time',
            'IsDNA': 'Total_IsDNA'
        }

        # --- STEP 2 PWP ---
        step2_pwp_agg = step2_pwp_sessions_summary.copy()
        if 'index' in step2_pwp_agg.columns:
            step2_pwp_agg.drop(columns='index', inplace=True)
        step2_pwp_agg = (
            step2_pwp_agg.groupby(['Run Number', 'Week Number'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step2_pwp_sessions_summary_mean = (
            step2_pwp_agg.groupby('Week Number', as_index=False)
            .mean(numeric_only=True)
        )

        pwp_sessions_weekly = pd.melt(
            step2_pwp_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )
        
        # convert minutes to hours
        step2_pwp_sessions_summary_mean['Total_Session_Time'] /= 60
        step2_pwp_sessions_summary_mean['Total_Admin_Time'] /= 60

        pwp_hours_weekly = pd.melt(
            step2_pwp_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Total_Session_Time', 'Total_Admin_Time'],
            var_name='variable',
            value_name='value')

        pwp_hours_weekly['variable'] = pwp_hours_weekly['variable'].replace({
        'Total_Session_Time': 'Session Time',
        'Total_Admin_Time': 'Admin Time'})

        # --- STEP 2 GROUP ---
        step2_group_agg = step2_group_sessions_summary.copy()
        if 'index' in step2_group_agg.columns:
            step2_group_agg.drop(columns='index', inplace=True)
        step2_group_agg = (
            step2_group_agg.groupby(['Run Number', 'Week Number'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step2_group_sessions_summary_mean = (
            step2_group_agg.groupby('Week Number', as_index=False)
            .mean(numeric_only=True)
        )

        group_sessions_weekly = pd.melt(
            step2_group_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )

        # convert minutes to hours
        step2_group_sessions_summary_mean['Total_Session_Time'] /= 60
        step2_group_sessions_summary_mean['Total_Admin_Time'] /= 60

        group_hours_weekly = pd.melt(
            step2_group_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Total_Session_Time', 'Total_Admin_Time'],
            var_name='variable',
            value_name='value'
        )

        group_hours_weekly['variable'] = pwp_hours_weekly['variable'].replace({
        'Total_Session_Time': 'Session Time',
        'Total_Admin_Time': 'Admin Time'})

        # --- STEP 3 CBT ---
        step3_cbt_agg = step3_cbt_sessions_summary.copy()
        if 'index' in step3_cbt_agg.columns:
            step3_cbt_agg.drop(columns='index', inplace=True)
        step3_cbt_agg = (
            step3_cbt_agg.groupby(['Run Number', 'Week Number'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step3_cbt_sessions_summary_mean = (
            step3_cbt_agg.groupby('Week Number', as_index=False)
            .mean(numeric_only=True)
        )

        cbt_sessions_weekly = pd.melt(
            step3_cbt_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )

        # convert minutes to hours
        step3_cbt_sessions_summary_mean['Total_Session_Time'] /= 60
        step3_cbt_sessions_summary_mean['Total_Admin_Time'] /= 60

        cbt_hours_weekly = pd.melt(
            step3_cbt_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Total_Session_Time', 'Total_Admin_Time'],
            var_name='variable',
            value_name='value'
        )

        cbt_hours_weekly['variable'] = cbt_hours_weekly['variable'].replace({
        'Total_Session_Time': 'Session Time',
        'Total_Admin_Time': 'Admin Time'})

        # --- STEP 3 COUNS ---
        step3_couns_agg = step3_couns_sessions_summary.copy()
        if 'index' in step3_couns_agg.columns:
            step3_couns_agg.drop(columns='index', inplace=True)
        step3_couns_agg = (
            step3_couns_agg.groupby(['Run Number', 'Week Number'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step3_couns_sessions_summary_mean = (
            step3_couns_agg.groupby('Week Number', as_index=False)
            .mean(numeric_only=True)
        )

        couns_sessions_weekly = pd.melt(
            step3_couns_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )

        # convert minutes to hours
        step3_couns_sessions_summary_mean['Total_Session_Time'] /= 60
        step3_couns_sessions_summary_mean['Total_Admin_Time'] /= 60

        couns_hours_weekly = pd.melt(
            step3_couns_sessions_summary_mean,
            id_vars=['Week Number'],
            value_vars=['Total_Session_Time', 'Total_Admin_Time'],
            var_name='variable',
            value_name='value'
        )

        couns_hours_weekly['variable'] = couns_hours_weekly['variable'].replace({
        'Total_Session_Time': 'Session Time',
        'Total_Admin_Time': 'Admin Time'})
      
        # --- Session Type Aggregation and Melt ---

        # Aggregation and renaming maps
        agg_mapping = {
            'Session Number': 'count',
            'Session Time': 'sum',
            'Admin Time': 'sum',
            'IsDNA': 'sum'
        }
        rename_map = {
            'Session Number': 'Session_Count',
            'Session Time': 'Total_Session_Time',
            'Admin Time': 'Total_Admin_Time',
            'IsDNA': 'Total_IsDNA'
        }

        # -- STEP 2 PWP --
        step2_pwp_type_agg = step2_pwp_session_type_summary.copy()
        if 'index' in step2_pwp_type_agg.columns:
            step2_pwp_type_agg.drop(columns='index', inplace=True)
        step2_pwp_type_agg = (
            step2_pwp_type_agg.groupby(['Run Number', 'Week Number', 'Session Type'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step2_pwp_type_mean = (
            step2_pwp_type_agg.groupby(['Week Number', 'Session Type'], as_index=False)
            .mean(numeric_only=True)
        )
        step2_pwp_type_mean = step2_pwp_type_mean[step2_pwp_type_mean["Week Number"] <= sim_duration_input - 1].reset_index(drop=True)
        step2_pwp_type_melt = pd.melt(
            step2_pwp_type_mean,
            id_vars=['Week Number', 'Session Type'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )

        # -- STEP 2 GROUP --
        step2_group_type_agg = step2_group_session_type_summary.copy()
        if 'index' in step2_group_type_agg.columns:
            step2_group_type_agg.drop(columns='index', inplace=True)
        step2_group_type_agg = (
            step2_group_type_agg.groupby(['Run Number', 'Week Number', 'Session Type'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step2_group_type_mean = (
            step2_group_type_agg.groupby(['Week Number', 'Session Type'], as_index=False)
            .mean(numeric_only=True)
        )
        step2_group_type_mean = step2_group_type_mean[step2_group_type_mean["Week Number"] <= sim_duration_input - 1].reset_index(drop=True)
        step2_group_type_melt = pd.melt(
            step2_group_type_mean,
            id_vars=['Week Number', 'Session Type'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )

        # -- STEP 3 CBT --
        step3_cbt_type_agg = step3_cbt_session_type_summary.copy()
        if 'index' in step3_cbt_type_agg.columns:
            step3_cbt_type_agg.drop(columns='index', inplace=True)
        step3_cbt_type_agg = (
            step3_cbt_type_agg.groupby(['Run Number', 'Week Number', 'Session Type'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step3_cbt_type_mean = (
            step3_cbt_type_agg.groupby(['Week Number', 'Session Type'], as_index=False)
            .mean(numeric_only=True)
        )
        step3_cbt_type_mean = step3_cbt_type_mean[step3_cbt_type_mean["Week Number"] <= sim_duration_input - 1].reset_index()
        step3_cbt_type_melt = pd.melt(
            step3_cbt_type_mean,
            id_vars=['Week Number', 'Session Type'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )

        # -- STEP 3 COUNS --
        step3_couns_type_agg = step3_couns_session_type_summary.copy()
        if 'index' in step3_couns_type_agg.columns:
            step3_couns_type_agg.drop(columns='index', inplace=True)
        step3_couns_type_agg = (
            step3_couns_type_agg.groupby(['Run Number', 'Week Number', 'Session Type'], as_index=False)
            .agg(agg_mapping)
            .rename(columns=rename_map)
        )
        step3_couns_type_mean = (
            step3_couns_type_agg.groupby(['Week Number', 'Session Type'], as_index=False)
            .mean(numeric_only=True)
        )
        step3_couns_type_mean = step3_couns_type_mean[step3_couns_type_mean["Week Number"] <= sim_duration_input - 1].reset_index()
        step3_couns_type_melt = pd.melt(
            step3_couns_type_mean,
            id_vars=['Week Number', 'Session Type'],
            value_vars=['Session_Count', 'Total_IsDNA'],
            var_name='variable',
            value_name='value'
        )


        ########## repeat above but for results dfs ##########
        # Define correct aggregation mapping based on the variable name
        agg_mapping = {
            'IsStep': 'sum',
            'IsDropout': 'sum'
        }

        # Dictionary of DataFrames to process
        aggregated_results_dfs = {
            'step2_pwp_results_summary': step2_pwp_results_summary,
            'step2_group_results_summary': step2_group_results_summary,
            'step3_cbt_results_summary': step3_cbt_results_summary,
            'step3_couns_results_summary': step3_couns_results_summary
        }

        aggregated_results = {}

        for name, df in aggregated_results_dfs.items():
            # Melt the DataFrame
            melted_df = pd.melt(df, id_vars=['Run Number',
                        'Week Number'], var_name='variable',
                        value_name='value')

            # Aggregating using the correct aggregation function based on variable
            def agg_func(x):
                # Get the correct aggregation function based on the variable
                variable = x.name  # This refers to the 'variable' column name
                if agg_mapping.get(variable) == 'mean':
                    return x.mean()
                elif agg_mapping.get(variable) == 'max':
                    return x.max()
                else:
                    return x.sum()  # Default sum if not found in the mapping

            # Apply the aggregation function based on variable
            aggregated_results_df = melted_df.groupby(['Run Number', 
                                    'Week Number', 'variable']).agg(
                {'value': agg_func}
            ).reset_index()

            # Store the result
            aggregated_results[name] = aggregated_results_df

        ########## repeat above but for waiting dfs ##########
        # Define correct aggregation mapping based on the variable name
        agg_mapping = {
            'Num Waiting': 'max',
            'Avg Wait': 'mean',
            'Max Wait': 'max',
            'Avg RTT': 'mean',
            'Max RTT': 'max'
            }

        # Dictionary of DataFrames to process
        aggregated_waiting_dfs = {
            'step2_pwp_waiting_summary': step2_pwp_waiting_summary,
            'step2_group_waiting_summary': step2_group_waiting_summary,
            'step3_cbt_waiting_summary': step3_cbt_waiting_summary,
            'step3_couns_waiting_summary': step3_couns_waiting_summary
        }

        aggregated_waiting = {}

        for name, df in aggregated_waiting_dfs.items():
            # Melt the DataFrame
            melted_df = pd.melt(df, id_vars=['Run Number', 'Week Number'],
                                var_name='variable', value_name='value')

            # Aggregating using the correct aggregation function based on variable
            def agg_func(x):
                # Get the correct aggregation function based on the variable
                variable = x.name  # This refers to the 'variable' column name
                if agg_mapping.get(variable) == 'mean':
                    return x.mean()
                elif agg_mapping.get(variable) == 'max':
                    return x.max()
                else:
                    return x.sum()  # Default sum if not found in the mapping

            # Apply the aggregation function based on variable
            aggregated_waiting_df = melted_df.groupby(['Run Number', 
                                                    'Week Number', 'variable']
                                                    ).agg({'value': agg_func}
                                                    ).reset_index()

            # Store the result
            aggregated_waiting[name] = aggregated_waiting_df

        ##### Extract final DataFrames #####

        pwp_sessions_summary = pwp_sessions_weekly #mean_sessions['step2_pwp_sessions_summary_mean']
        group_sessions_summary = group_sessions_weekly #mean_sessions['step2_group_sessions_summary_mean']
        cbt_sessions_summary = cbt_sessions_weekly #mean_sessions['step3_cbt_sessions_summary_mean']
        couns_sessions_summary = couns_sessions_weekly #mean_sessions['step3_couns_sessions_summary_mean']

        pwp_results_summary = aggregated_results['step2_pwp_results_summary']
        group_results_summary = aggregated_results['step2_group_results_summary']
        cbt_results_summary = aggregated_results['step3_cbt_results_summary']
        couns_results_summary = aggregated_results['step3_couns_results_summary']

        ##### Waiting Lists #####
        
        pwp_waiting_summary = aggregated_waiting['step2_pwp_waiting_summary']

        #st.write(pwp_waiting_summary)

        # get mean across all runs
        pwp_waiting_summary = (
                                pwp_waiting_summary
                                .groupby(['Week Number', 'variable'], as_index=False)['value']
                                .mean()
                                )
        
        #st.write(pwp_waiting_summary)
        
        # isolate RTT data
        pwp_rtt_summary = pwp_waiting_summary[pwp_waiting_summary[
                        'variable'].isin(['Avg RTT','Max RTT'])]

        # isolate waiting list data
        pwp_waiting_summary = pwp_waiting_summary[pwp_waiting_summary[
                                'variable'].isin(['Num Waiting','Avg Wait','Max Wait'])]
        
        group_waiting_summary = aggregated_waiting['step2_group_waiting_summary']
        
        # get mean across all runs
        group_waiting_summary = (
                                group_waiting_summary
                                .groupby(['Week Number', 'variable'], as_index=False)['value']
                                .mean()
                                )
        
        #st.write(group_waiting_summary)
        
        # isolate RTT data
        group_rtt_summary = group_waiting_summary[group_waiting_summary[
                        'variable'].isin(['Avg RTT','Max RTT'])]

        # isolate waiting list data
        group_waiting_summary = group_waiting_summary[group_waiting_summary[
                                'variable'].isin(['Num Waiting','Avg Wait','Max Wait'])]
        
        cbt_waiting_summary = aggregated_waiting['step3_cbt_waiting_summary']
        
        # get mean across all runs
        cbt_waiting_summary = (
                                cbt_waiting_summary
                                .groupby(['Week Number', 'variable'], as_index=False)['value']
                                .mean()
                                )
        
        #st.write(cbt_waiting_summary)
        
        # isolate RTT data
        cbt_rtt_summary = cbt_waiting_summary[cbt_waiting_summary[
                        'variable'].isin(['Avg RTT','Max RTT'])]

        # isolate waiting list data
        cbt_waiting_summary = cbt_waiting_summary[cbt_waiting_summary[
                                'variable'].isin(['Num Waiting','Avg Wait','Max Wait'])]
        
        couns_waiting_summary = aggregated_waiting['step3_couns_waiting_summary']
        
        # get mean across all runs
        couns_waiting_summary = (
                                couns_waiting_summary
                                .groupby(['Week Number', 'variable'], as_index=False)['value']
                                .mean()
                                )
        
        #st.write(couns_waiting_summary)
        
        # isolate RTT data
        couns_rtt_summary = couns_waiting_summary[couns_waiting_summary[
                        'variable'].isin(['Avg RTT','Max RTT'])]

        # isolate waiting list data
        couns_waiting_summary = couns_waiting_summary[couns_waiting_summary[
                                'variable'].isin(['Num Waiting','Avg Wait','Max Wait'])]
 
        ##### merge results and sessions #####
        pwp_combined_summary = pd.concat([pwp_sessions_summary,
                                        pwp_results_summary,
                                        pwp_waiting_summary],
                                        ignore_index=True).reset_index()
        #st.write(pwp_combined_summary)

        group_combined_summary = pd.concat([group_sessions_summary,
                                        group_results_summary,
                                        group_waiting_summary],
                                        ignore_index=True).reset_index()
        cbt_combined_summary = pd.concat([cbt_sessions_summary,
                                        cbt_results_summary,
                                        cbt_waiting_summary],
                                        ignore_index=True).reset_index()
        couns_combined_summary = pd.concat([couns_sessions_summary,
                                        couns_results_summary,
                                        couns_waiting_summary],
                                        ignore_index=True).reset_index()
        # get rid of any sessions recorded beyond the simulation period
        pwp_combined_summary = pwp_combined_summary[pwp_combined_summary[  
                                "Week Number"] <= sim_duration_input-1
                                ].reset_index()
        group_combined_summary = group_combined_summary[group_combined_summary[
                                "Week Number"] <= sim_duration_input-1].reset_index()
        cbt_combined_summary = cbt_combined_summary[cbt_combined_summary[
                                "Week Number"] <= sim_duration_input-1].reset_index()
        couns_combined_summary = couns_combined_summary[couns_combined_summary[
                                "Week Number"] <= sim_duration_input-1].reset_index()
        # get rid of week zero as no sessions run until week 1 when assessments come through
        # pwp_combined_summary = pwp_combined_summary[pwp_combined_summary[
        #                                             "Week Number"] != 0]
        # group_combined_summary = group_combined_summary[group_combined_summary[
        #                                             "Week Number"] != 0]
        # cbt_combined_summary = cbt_combined_summary[cbt_combined_summary[
        #                                             "Week Number"] != 0]
        # couns_combined_summary = couns_combined_summary[couns_combined_summary[
        #                                             "Week Number"] != 0]
        
        ##### Staff Non-clinical Activity #####
        # turn into hours and divide by number of sim runs to get average across all the runs
        staff_weekly_dfs['Supervision Hrs'] = staff_weekly_dfs['Supervision Mins'
                                                    ]/(60*number_of_runs_input)
        staff_weekly_dfs['Break Hrs'] = staff_weekly_dfs['Break Mins'
                                                    ]/(60*number_of_runs_input)
        staff_weekly_dfs['Wellbeing Hrs'] = staff_weekly_dfs['Wellbeing Mins'
                                                    ]/(60*number_of_runs_input)
        staff_weekly_dfs['Huddle Hrs'] = staff_weekly_dfs['Huddle Mins'
                                                    ]/(60*number_of_runs_input)
        staff_weekly_dfs['CPD Hrs'] = staff_weekly_dfs['CPD Mins'
                                                    ]/(60*number_of_runs_input)
        
        pwp_weekly_act_dfs = staff_weekly_dfs.loc[staff_weekly_dfs[
                'Job Role'] == 'pwp'].reset_index()
        
        pwp_weekly_activity = pd.melt(pwp_weekly_act_dfs, value_vars=[
                                                                'Supervision Hrs',
                                                                'Break Hrs',
                                                                'Wellbeing Hrs',
                                                                'Huddle Hrs',
                                                                'CPD Hrs'],
                                                                id_vars=[
                                                                'Week Number'])
        
        cbt_weekly_act_dfs = staff_weekly_dfs.loc[staff_weekly_dfs[
                'Job Role'] == 'cbt'].reset_index(drop=True)
        
        cbt_weekly_activity = pd.melt(cbt_weekly_act_dfs, value_vars=[
                                                                'Supervision Hrs',
                                                                'Break Hrs',
                                                                'Wellbeing Hrs',
                                                                'Huddle Hrs',
                                                                'CPD Hrs'],
                                                                id_vars=[
                                                                'Week Number'])
        couns_weekly_act_dfs = staff_weekly_dfs.loc[staff_weekly_dfs[
                'Job Role'] == 'couns'].reset_index(drop=True)
        
        couns_weekly_activity = pd.melt(couns_weekly_act_dfs, value_vars=[
                                                                'Supervision Hrs',
                                                                'Break Hrs',
                                                                'Wellbeing Hrs',
                                                                'Huddle Hrs',
                                                                'CPD Hrs'],
                                                                id_vars=[
                                                                'Week Number'])
        with st.expander("See explanation"):
            st.write('This Simulation is designed to replicate the flow '
                     'of patients through the Talking Therapies Assessment and'
                     'Treatment Pathway.')
          
        ########## Job Plans Tab ##########
        ##### pwp Practitoner #####
        
        # get time values from sessions dataframe and convert to hours - divide by 60 * sim duration to get average across all runs when summed up
        # pwp
        pwp_sessions_weekly_summary = pwp_sessions_summary[pwp_sessions_summary
                                        ['variable'].isin(['Session Time'
                                        ,'Admin Time'])]
        #pwp_sessions_weekly_summary.drop('Run Number', axis=1)
        pwp_sessions_weekly_summary[pwp_sessions_weekly_summary.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])] = pwp_sessions_weekly_summary[
                                    pwp_sessions_weekly_summary.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])].div(60*number_of_runs_input
                                    ).round()
               
        # group
        group_sessions_weekly_summary = group_sessions_summary[
                                        group_sessions_summary['variable'].isin(
                                        ['Session Time','Admin Time'])]
        group_sessions_weekly_summary[group_sessions_weekly_summary.select_dtypes(
                        include="number").columns.difference(["Week Number"])] = \
                        group_sessions_weekly_summary[
                        group_sessions_weekly_summary.select_dtypes(
                        include="number").columns.difference(["Week Number"]
                        )].div(60*number_of_runs_input).round()
        
        # get sessions by type and calculate average based on number of runs
        group_sessions_weekly_bytype = step2_group_type_melt[
                                        step2_group_type_melt['variable'
                                        ].isin(['Session_Count','Total_IsDNA'])]
        #group_sessions_weekly_bytype.drop('Run Number', axis=1)
        group_sessions_weekly_bytype[group_sessions_weekly_bytype.select_dtypes(
                        include="number").columns.difference(["Week Number"])] = \
                        group_sessions_weekly_bytype[
                        group_sessions_weekly_bytype.select_dtypes(
                        include="number").columns.difference(["Week Number"])
                        ].div(number_of_runs_input).round()
        # cbt
        cbt_sessions_weekly_summary = cbt_sessions_summary[cbt_sessions_summary[
                                'variable'].isin(['Session Time','Admin Time'])]
        cbt_sessions_weekly_summary[cbt_sessions_weekly_summary.select_dtypes(
                        include="number").columns.difference(["Week Number"])] = \
                        cbt_sessions_weekly_summary[
                        cbt_sessions_weekly_summary.select_dtypes(
                        include="number").columns.difference(["Week Number"])
                        ].div(60*number_of_runs_input).round()
        # get sessions by type and calculate average based on number of runs
        cbt_sessions_weekly_bytype = step3_cbt_type_melt[
                                    step3_cbt_type_melt['variable'
                                    ].isin(['Session_Count','Total_IsDNA'])]
        #cbt_sessions_weekly_bytype.drop('Run Number', axis=1)
        cbt_sessions_weekly_bytype[cbt_sessions_weekly_bytype.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])] = cbt_sessions_weekly_bytype[
                                    cbt_sessions_weekly_bytype.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])].div(number_of_runs_input
                                    ).round()
        # couns
        couns_sessions_weekly_summary = couns_sessions_summary[
                                        couns_sessions_summary['variable'].isin(
                                        ['Session Time','Admin Time'])]
        couns_sessions_weekly_summary[couns_sessions_weekly_summary.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])] = couns_sessions_weekly_summary[
                                    couns_sessions_weekly_summary.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])].div(60*number_of_runs_input
                                    ).round()
        # get sessions by type and calculate average based on number of runs
        couns_sessions_weekly_bytype = step3_couns_type_melt[
                                        step3_couns_type_melt['variable'
                                        ].isin(['Session_Count','Total_IsDNA'])]
        #couns_sessions_weekly_bytype.drop('Run Number', axis=1)
        couns_sessions_weekly_bytype[couns_sessions_weekly_bytype.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])] = couns_sessions_weekly_bytype[
                                    couns_sessions_weekly_bytype.select_dtypes(
                                    include="number").columns.difference(
                                    ["Week Number"])].div(number_of_runs_input
                                    ).round()     
                
        # combine pwp and group as all delivered by pwp
        pwp_group_sessions_combined = pd.concat([pwp_sessions_weekly_summary,
                                        group_sessions_weekly_summary]
                                        ,ignore_index=True)
        
        # get time value from asst dataframe
        pwp_asst_weekly_summary = asst_weekly_dfs[['Week Number'
                                                ,'Referral Screen Hrs'
                                                ,'TA Hrs']]
        # get average across all runs
        pwp_asst_weekly_summary[['Referral Screen Hrs','TA Hrs']
                                ] = pwp_asst_weekly_summary[[
                                'Referral Screen Hrs','TA Hrs']
                                ]/number_of_runs_input
        pwp_asst_weekly_summary[['Referral Screen Hrs','TA Hrs']
                                ] = pwp_asst_weekly_summary[[
                                'Referral Screen Hrs','TA Hrs']]*0.87 # 87% of TA's done by pwp

        pwp_asst_weekly_summary = pd.melt(pwp_asst_weekly_summary, value_vars=[
                                                            'Referral Screen Hrs',
                                                            'TA Hrs'],
                                                            id_vars=[
                                                            'Week Number'])

        ##### cbt #####

        cbt_asst_weekly_summary = asst_weekly_dfs[['Week Number','TA Hrs']]
        # get average across all runs
        cbt_asst_weekly_summary['TA Hrs'] = asst_weekly_dfs['TA Hrs'
                                            ]/number_of_runs_input
        cbt_asst_weekly_summary['TA Hrs'] = cbt_asst_weekly_summary[
                                            'TA Hrs']*0.11 # 11% of TA's done by cbt

        cbt_asst_weekly_summary = pd.melt(cbt_asst_weekly_summary, value_vars=[
                                                                 'TA Hrs'],
                                                                 id_vars=[
                                                                'Week Number'])
        ##### cbt #####

        couns_asst_weekly_summary = asst_weekly_dfs[['Week Number','TA Hrs']]
        couns_asst_weekly_summary['TA Hrs'] = couns_asst_weekly_summary[
                                            'TA Hrs']/number_of_runs_input
        couns_asst_weekly_summary['TA Hrs'] = couns_asst_weekly_summary[
                                            'TA Hrs']*0.02 # 2% of TA's done by couns

        couns_asst_weekly_summary = pd.melt(couns_asst_weekly_summary,
                                            value_vars=['TA Hrs'],id_vars=[
                                            'Week Number'])
      
        ##### bring all the clinical and non-clinical activity data together
        pwp_hours_weekly_summary = pd.concat([pwp_hours_weekly
                                            ,group_hours_weekly
                                            ,pwp_asst_weekly_summary
                                            ,pwp_weekly_activity
                                            ],ignore_index=True).reset_index()
        # get rid of sessions that go beyond sim duration
        pwp_hours_weekly_summary = pwp_hours_weekly_summary[
                                    pwp_hours_weekly_summary[
                                    "Week Number"] <=sim_duration_input-1]
           
        cbt_hours_weekly_summary = pd.concat([cbt_hours_weekly,
                                            cbt_asst_weekly_summary,
                                            cbt_weekly_activity]
                                            ,ignore_index=True)
        # get rid of sessions that go beyond sim duration
        cbt_hours_weekly_summary = cbt_hours_weekly_summary[
                                    cbt_hours_weekly_summary[
                                    "Week Number"] <=sim_duration_input-1]

        couns_hours_weekly_summary = pd.concat([couns_hours_weekly,
                                                couns_asst_weekly_summary
                                                ,couns_weekly_activity]
                                                ,ignore_index=True)
        # get rid of sessions that go beyond sim duration
        couns_hours_weekly_summary = couns_hours_weekly_summary[
                                    couns_hours_weekly_summary[
                                    "Week Number"] <=sim_duration_input-1]
        
        
        ########## Referrals & Assessments ##########
        
        asst_weekly_summary_filtered = asst_weekly_summary[['Run Number'
                                                            ,'Week Number',
                                                            'Referrals Received'
                                                            ,'TA Avg Wait']]
        
        #st.write(asst_weekly_summary_filtered)
        
        asst_weekly_summary_max_wait = asst_weekly_summary[['Week Number',
                                                            'TA Max Wait']]

        asst_referrals_col1_unpivot = pd.melt(asst_weekly_summary_filtered,
                                                        value_vars=[
                                                        'Referrals Received',
                                                        'TA Avg Wait'],
                                                        id_vars=['Run Number',
                                                        'Week Number'])
        
        asst_referrals_max_unpivot = pd.melt(asst_weekly_summary_max_wait,
                                            value_vars=['TA Max Wait'],
                                            id_vars=['Week Number']
                                            ).reset_index(drop=True)
        
        asst_referrals_col2_unpivot = pd.melt(asst_weekly_summary, value_vars=[
                                                    'Referrals Rejected',
                                                    'TA Waiting List'],
                                                    id_vars=['Run Number',
                                                    'Week Number'])
        
        #st.write(asst_weekly_summary)
        
        asst_referrals_col3_unpivot = pd.melt(asst_weekly_summary, value_vars=[
                                                    'Accepted Referrals',
                                                    'TA 6W PC'],
                                                    id_vars=['Run Number',
                                                    'Week Number'])
        
        weekly_avg_prev = (
                            pd.melt(asst_weekly_summary, 
                                    id_vars=['Run Number', 'Week Number'], 
                                    value_vars=['Prev PC'])
                            .groupby(['Week Number', 'variable'], as_index=False)['value']
                            .mean()
                        )
        
        #st.write(weekly_avg_prev)
        
        ########## Caseloads ##########

        caseload_weekly_dfs['caseload_used'] = caseload_weekly_dfs[
                                                'caseload_cap'] - \
                                                caseload_weekly_dfs[
                                                'caseload_level']

        caseload_avg_df = caseload_weekly_dfs.groupby(['Week Number',
                        'caseload_id'])['caseload_used'].mean().reset_index()
        #st.write(caseload_avg_df)
        #caseload_weekly_dfs['Caseload Level'] = caseload_weekly_dfs['Caseload Level']/number_of_runs_input

        pwp_caseload_weekly_summary = caseload_avg_df[caseload_avg_df[
                                    'caseload_id'].str.startswith('pwp')]
        cbt_caseload_weekly_summary = caseload_avg_df[caseload_avg_df[
                                    'caseload_id'].str.startswith('cbt')]
        couns_caseload_weekly_summary = caseload_avg_df[caseload_avg_df[
                                    'caseload_id'].str.startswith('couns')]
        
        ###########################
        ## Dashboard Starts Here ##
        ###########################
        
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Screening & Assessment"
                                                ,"Step 2","Step 3",'RTT'
                                                ,"Job Plans","Caseloads"])
        
        # ########## Screening & Assessment Tab ##########
        
        with tab1:

            col1, col2, col3 = st.columns(3)

            with col1:
            
                for a, list_name in enumerate(asst_referrals_col1_unpivot[
                                            'variable'].unique()):

                    if list_name == 'Referrals Received':
                        section_title = '### Referrals'
                    elif list_name == 'TA Avg Wait':
                        section_title = '### Assessment'

                    if list_name == 'Referrals Received':
                        chart_title = list_name
                    elif list_name == 'TA Avg Wait':
                        chart_title = 'TA Waiting Times'

                    if list_name == 'Referrals Received':
                        axis_title = 'Referrals'
                    elif list_name == 'TA Avg Wait':
                        axis_title = 'TA Avg Wait'

                    st.markdown(section_title)

                    asst_referrals_col1_filtered = asst_referrals_col1_unpivot[
                                        asst_referrals_col1_unpivot["variable"]
                                        ==list_name]

                    weekly_avg_col1 = asst_referrals_col1_filtered.groupby([
                                        'Week Number', 'variable'])['value'
                                        ].mean().reset_index()
                    
                    fig_asst_1 = px.line(
                                weekly_avg_col1,
                                x="Week Number",
                                #color="Run Number",
                                #line_dash="Run",
                                y="value",
                                labels={
                                        "value": axis_title
                                       },
                                height=425,
                                width=500,
                                title=f'{chart_title} by Week'
                                )
                    
                    fig_asst_1.update_traces(line=dict(width=3, color='blue'))
                              
                    
                    #fig_asst_1.update_traces(line=dict(dash='dot'))
                    
                    if list_name == 'TA Avg Wait':

                        fig_asst_1.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))
                        
                        weekly_max_col1 = asst_referrals_max_unpivot.loc[
                        asst_referrals_max_unpivot['variable'] == 'TA Max Wait'
                        ].groupby(['Week Number', 'variable'])['value'
                                                ].mean().reset_index()
                    
                        fig_asst_1.add_trace(
                                go.Scatter(x=weekly_avg_col1["Week Number"],
                                        y=weekly_max_col1["value"], name='Maximum',
                                        line=dict(width=3,color='red')))
                        
                    else:
                        pass

                    # fig_asst_1.add_trace(
                    #             go.Scatter(x=weekly_avg_col1["Week Number"],
                    #                     y=weekly_avg_col1["value"], name='Average',
                    #                     line=dict(width=3,color='blue')))
                           
                    # get rid of 'variable' prefix resulting from df.melt
                    fig_asst_1.for_each_annotation(lambda a: a.update(
                                            text=a.text.split("=")[1]))

                    fig_asst_1.update_layout(title_x=0.3,font=dict(size=10))

                    # fig_asst_1.update_layout(
                    #     legend=dict(
                    #         x=0.8,  # Horizontal position (0 to 1, where 0 is left and 1 is right)
                    #         y=0.9,  # Vertical position (0 to 1, where 0 is bottom and 1 is top)
                    #         xanchor='center',  # Horizontal anchor point
                    #         yanchor='top'      # Vertical anchor point
                    #     )
                    # )

                    st.plotly_chart(fig_asst_1, key=f"chart_{list_name}_{a}"
                                                ,use_container_width=True)

                    st.divider()

            with col2:
                           
                for b, list_name in enumerate(asst_referrals_col2_unpivot[
                                                    'variable'].unique()):

                    asst_referrals_col2_filtered = asst_referrals_col2_unpivot[
                                        asst_referrals_col2_unpivot["variable"]
                                        ==list_name]
                    
                    weekly_avg_col2 = asst_referrals_col2_filtered.groupby([
                                                    'Week Number','variable']
                                                    )['value'].mean(
                                                    ).reset_index()
                    
                    if list_name == 'Referrals Rejected':
                        axis_title = 'Referrals'
                    elif list_name == 'TA Waiting List':
                        axis_title = 'Patients'
                    
                    st.subheader('') 

                    if list_name == 'Referrals Rejected':
                    
                        fig_asst_2 = px.line(
                                    weekly_avg_col2,
                                    x="Week Number",
                                    #color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": axis_title
                                            },
                                        height=425,
                                        width=500,
                                        title=f'{list_name} by Week'
                                        )
                            
                        fig_asst_2.update_traces(showlegend=False, line=dict(width=3, color='blue'))

                    else:

                        fig_asst_2 = px.line(
                                    asst_referrals_col2_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": axis_title
                                            },
                                        height=425,
                                        width=500,
                                        title=f'{list_name} by Week'
                                        )
                            
                        fig_asst_2.update_traces(line=dict(dash='dot'))
                   
                        fig_asst_2.add_trace(
                                    go.Scatter(x=weekly_avg_col2["Week Number"],
                                            y=weekly_avg_col2["value"], name='Average',
                                            line=dict(width=3,color='blue')))
                        
                    # get rid of 'variable' prefix resulting from df.melt
                    fig_asst_2.for_each_annotation(lambda a: a.update(text=a.text.split
                                                            ("=")[1]))

                    fig_asst_2.update_layout(title_x=0.3,font=dict(size=10))
                    #fig.

                    st.plotly_chart(fig_asst_2, key=f"chart_{list_name}_{b}"
                                                    ,use_container_width=True)

                    st.divider()

        with col3:

            for i, list_name in enumerate(asst_referrals_col3_unpivot['variable'].unique()):
                asst_referrals_col3_filtered = asst_referrals_col3_unpivot[
                    asst_referrals_col3_unpivot["variable"] == list_name]

                weekly_avg_col3 = (
                    asst_referrals_col3_filtered.groupby(['Week Number', 'variable'])['value']
                    .mean().reset_index()
                )

                if list_name == 'Accepted Referrals':
                    axis_title = 'Referrals'
                elif list_name == 'TA 6W PC':
                    axis_title = '%'
                else:
                    axis_title = 'Value'

                st.subheader('')

                fig_asst_3 = px.line(
                    weekly_avg_col3,
                    x="Week Number",
                    y="value",
                    labels={"value": axis_title},
                    height=425,
                    width=500,
                    title=f'{list_name} by Week'
                )

                if list_name == 'TA 6W PC':                
                    fig_asst_3.update_traces(name='6 Week RTA', showlegend=True, line=dict(width=3, color='blue'))
                else:
                    fig_asst_3.update_traces(showlegend=False, line=dict(width=3, color='blue'))

                if list_name == 'TA 6W PC' and 'weekly_avg_prev' in locals():
                    fig_asst_3.add_trace(
                        go.Scatter(x=weekly_avg_prev["Week Number"],
                                y=weekly_avg_prev["value"],
                                name='Prevalence',
                                line=dict(width=3, color='green'))
                    )
                    fig_asst_3.update_layout(title_text="% RTA Within 6 Weeks & Prevalence")

                fig_asst_3.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
                
                fig_asst_3.update_layout(title_x=0.3, font=dict(size=10))

                st.plotly_chart(fig_asst_3, key=f"chart_{list_name}_{i}", use_container_width=True)
                
                st.divider()


        # ########## step2 Tab ##########

        ########## pwp ##########
        with tab2:

            st.subheader('Step 2')

            col1, col2 = st.columns(2)

            with col1:

                st.subheader('Psychological Wellbeing Practitioner - 1:1')
            
                for c, list_name in enumerate(pwp_combined_summary['variable']
                                            .unique()):
                  
                    if list_name == 'Session_Count':
                        section_title = 'Sessions'
                    elif list_name == 'Num Waiting':
                        section_title = 'Waiting List'

                    if list_name == 'Session_Count':
                        axis_title = 'Sessions'
                    elif list_name == 'Num Waiting':
                        axis_title = 'Patients'

                    pwp_sessions_weekly_type_filtered = step2_pwp_type_melt[
                                        step2_pwp_type_melt["variable"]==list_name]
                    
                    #st.write(pwp_sessions_weekly_type_filtered)
                    
                    pwp_combined_col1_filtered = pwp_combined_summary[
                                        pwp_combined_summary["variable"]==list_name]
                    
                    #st.write(pwp_combined_col1_filtered)
                    
                    if list_name == 'Session_Count':
                        section_title = 'Sessions'

                        custom_colors = {'First': "#2ca02c",
                                        'Follow-Up': "#98df8a"}
                        
                        custom_stack_order = ["First", "Follow-Up"]  # Order from bottom to top
                    
                        fig1 = px.histogram(pwp_sessions_weekly_type_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color='Session Type',
                                            color_discrete_map=custom_colors, #custom_colors,
                                            category_orders={'Session Type': 
                                                            custom_stack_order},
                                            title=f'Number of Sessions per Week')
                        
                        fig1.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig1.update_traces(marker_line_color='black', marker_line_width=1)

                        fig1.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig1, key=f"pwp_chart_{list_name}_{c}"
                                                    ,use_container_width=True)

                        st.divider()

                    elif list_name == 'Num Waiting':
                        section_title = 'Waiting List'

                        # get the average waiting list across all the runs
                        weekly_avg_col1 = pwp_combined_col1_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig2 = px.line(
                                    weekly_avg_col1,
                                    x="Week Number",
                                    #color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Patients'
                                        },
                                    height=425,
                                    width=500,
                                    title='Number of Patients Waiting by Week'
                                    )
                        
                        #fig2.update_traces(line=dict(dash='dot'))

                        fig2.update_layout(showlegend=False)

                        fig2.update_traces(line=dict(width=3, color='blue'))
                                            
                        # get rid of 'variable' prefix resulting from df.melt
                        fig2.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                       
                        fig2.update_layout(title_x=0.3,font=dict(size=10))
                        #fig.

                        st.plotly_chart(fig2, key=f"pwp_chart_{list_name}_{c}"
                                                    ,use_container_width=True)

                        st.divider()

            with col2:            
                              
                if list_name == 'Total_IsDNA':
                    axis_title = 'DNAs'
                elif list_name == 'Avg Wait':
                    axis_title = 'Weeks'

                st.subheader('')

                for d, list_name in enumerate(pwp_combined_summary['variable']
                                            .unique()):

                    pwp_sessions_weekly_type_filtered = step2_pwp_type_melt[
                                        step2_pwp_type_melt["variable"]==list_name]
                    
                    pwp_combined_col2_filtered = pwp_combined_summary[
                                        pwp_combined_summary["variable"]==
                                        list_name]
                    
                    pwp_combined_col2_max = pwp_combined_summary[
                                        pwp_combined_summary["variable"]==
                                        'Max Wait']
                    
                    if list_name == 'Total_IsDNA':

                        custom_colors_red = {
                                            'First': "#d62728", 
                                            'Follow-Up': "#ff9896"
                                            }
                        custom_stack_order_red = ["First", "Follow-Up"] # Order from bottom to top
                        
                        section_title = ''
                    
                        fig3 = px.histogram(pwp_sessions_weekly_type_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color='Session Type',
                                            color_discrete_map=custom_colors_red, #custom_colors,
                                            category_orders={'Session Type': 
                                                            custom_stack_order_red},
                                            title=f'Number of DNAs per Week')
                        
                        fig3.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig3.update_traces(marker_line_color='black', marker_line_width=1)

                        fig3.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig3, key=f"pwp_chart_{list_name}_{d}",
                                                    use_container_width=True)

                        st.divider()

                    elif list_name == 'Avg Wait':

                        section_title = ''

                        # get the average waiting time across all the runs
                        weekly_avg_col2 = pwp_combined_col2_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()

                        fig4 = px.line(
                                    weekly_avg_col2,
                                    x="Week Number",
                                    #color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Weeks'
                                        },
                                    height=425,
                                    width=500,
                                    title='Waiting Time by Week'
                                    )
                        
                        # Force the first trace to appear in the legend
                        fig4.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))

                        # get the average waiting time across all the runs
                        weekly_max_col2 = pwp_combined_col2_max.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                                                
                        fig4.add_trace(
                                    go.Scatter(x=weekly_max_col2["Week Number"],
                                            y=weekly_max_col2["value"], name='Maximum',
                                            line=dict(width=3,color='red')))
                        
                        # add line for 18 week target
                        fig4.add_trace(
                                go.Scatter(x=weekly_avg_col2["Week Number"],
                                        y=np.repeat(18,sim_duration_input*2),
                                        name='18 Week RTT',line=dict(width=3,
                                        color='green')))
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig4.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                        
                        fig4.update_layout(title_x=0.3,font=dict(size=10))

                        st.plotly_chart(fig4, key=f"pwp_chart_{list_name}_{d}",
                                        use_container_width=True)

                        st.divider()

            ########## groups ##########

            col3, col4 = st.columns(2)

            with tab2:

                col3, col4 = st.columns(2)

                with col3:

                    st.subheader('Psychological Wellbeing Practitioner - Group')
                
                    for c, list_name in enumerate(group_combined_summary['variable']
                                                .unique()):
                    
                        if list_name == 'Session_Count':
                            section_title = 'Sessions'
                        elif list_name == 'Num Waiting':
                            section_title = 'Waiting List'

                        if list_name == 'Session_Count':
                            axis_title = 'Sessions'
                        elif list_name == 'Num Waiting':
                            axis_title = 'Patients'

                        group_sessions_weekly_type_filtered = step2_group_type_melt[
                                            step2_group_type_melt["variable"]==list_name]
                        
                        #st.write(group_sessions_weekly_type_filtered)
                        
                        group_combined_col3_filtered = group_combined_summary[
                                            group_combined_summary["variable"]==list_name]
                        
                        if list_name == 'Session_Count':
                            section_title = 'Sessions'

                            custom_colors = {'First': "#2ca02c",
                                            'Follow-Up': "#98df8a"}
                            
                            custom_stack_order = ["First", "Follow-Up"]  # Order from bottom to top
                        
                            fig1 = px.histogram(group_sessions_weekly_type_filtered, 
                                                x='Week Number',
                                                y='value',
                                                nbins=sim_duration_input,
                                                labels={'value': 'Sessions'},
                                                color='Session Type',
                                                color_discrete_map=custom_colors, #custom_colors,
                                                category_orders={'Session Type': 
                                                                custom_stack_order},
                                                title=f'Number of Sessions per Week')
                            
                            fig1.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                            
                            fig1.update_traces(marker_line_color='black', marker_line_width=1)

                            fig1.update_yaxes(title_text="Sessions")

                            st.plotly_chart(fig1, key=f"group_chart_{list_name}_{c}"
                                                        ,use_container_width=True)

                            st.divider()

                        elif list_name == 'Num Waiting':
                            section_title = 'Waiting List'

                            # get the average waiting list across all the runs
                            weekly_avg_col3 = group_combined_col3_filtered.groupby(['Week Number',
                                                            'variable'])['value'].mean(
                                                            ).reset_index()
                            
                            fig2 = px.line(
                                        weekly_avg_col3,
                                        x="Week Number",
                                        #color="Run Number",
                                        #line_dash="Run",
                                        y="value",
                                        labels={
                                                "value": 'Patients'
                                            },
                                        height=425,
                                        width=500,
                                        title='Number of Patients Waiting by Week'
                                        )
                            
                            #fig2.update_traces(line=dict(dash='dot'))

                            fig2.update_layout(showlegend=False)

                            fig2.update_traces(line=dict(width=3, color='blue'))
                                                
                            # get rid of 'variable' prefix resulting from df.melt
                            fig2.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                    ("=")[1]))
                        
                            fig2.update_layout(title_x=0.3,font=dict(size=10))
                            #fig.

                            st.plotly_chart(fig2, key=f"group_chart_{list_name}_{c}"
                                                        ,use_container_width=True)

                            st.divider()

                with col4:            
                                
                    if list_name == 'Total_IsDNA':
                        axis_title = 'DNAs'
                    elif list_name == 'Avg Wait':
                        axis_title = 'Weeks'

                    st.subheader('')

                    for d, list_name in enumerate(group_combined_summary['variable']
                                                .unique()):

                        group_sessions_weekly_type_filtered = step2_group_type_melt[
                                            step2_group_type_melt["variable"]==list_name]
                        
                        group_combined_col4_filtered = group_combined_summary[
                                            group_combined_summary["variable"]==
                                            list_name]
                        
                        group_combined_col4_max = group_combined_summary[
                                            group_combined_summary["variable"]==
                                            'Max Wait']
                        
                        if list_name == 'Total_IsDNA':

                            custom_colors_red = {
                                            'First': "#d62728", 
                                            'Follow-Up': "#ff9896"
                                            }
                            custom_stack_order_red = ["First", "Follow-Up"] # Order from bottom to top
                            
                            section_title = ''
                        
                            fig3 = px.histogram(group_sessions_weekly_type_filtered, 
                                                x='Week Number',
                                                y='value',
                                                nbins=sim_duration_input,
                                                labels={'value': 'Sessions'},
                                                color='Session Type',
                                                color_discrete_map=custom_colors_red, #custom_colors,
                                                category_orders={'Session Type': 
                                                                custom_stack_order_red},
                                                title=f'Number of DNAs per Week')
                            
                            fig3.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                            
                            fig3.update_traces(marker_line_color='black', marker_line_width=1)

                            fig3.update_yaxes(title_text="Sessions")

                            st.plotly_chart(fig3, key=f"group_chart_{list_name}_{d}",
                                                        use_container_width=True)

                            st.divider()

                        elif list_name == 'Avg Wait':

                            section_title = ''

                             # get the average waiting time across all the runs
                            weekly_avg_col4 = group_combined_col4_filtered.groupby(['Week Number',
                                                            'variable'])['value'].mean(
                                                            ).reset_index()

                            fig4 = px.line(
                                        weekly_avg_col4,
                                        x="Week Number",
                                        #color="Run Number",
                                        #line_dash="Run",
                                        y="value",
                                        labels={
                                                "value": 'Weeks'
                                            },
                                        height=425,
                                        width=500,
                                        title='Waiting Time by Week'
                                        )
                            
                            # Force the first trace to appear in the legend
                            fig4.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))
                         
                            # get the average waiting time across all the runs
                            weekly_max_col4 = group_combined_col4_max.groupby(['Week Number',
                                                            'variable'])['value'].mean(
                                                            ).reset_index()
                             
                            fig4.add_trace(
                                        go.Scatter(x=weekly_max_col4["Week Number"],
                                                y=weekly_max_col4["value"], name='Maximum',
                                                line=dict(width=3,color='red')))
                            
                            # add line for 18 week RTT
                            fig4.add_trace(
                                go.Scatter(x=weekly_avg_col2["Week Number"],
                                        y=np.repeat(18,sim_duration_input*2),
                                        name='18 Week RTT',line=dict(width=3,
                                        color='green')))
                            
                            # get rid of 'variable' prefix resulting from df.melt
                            fig4.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                    ("=")[1]))
                            
                            fig4.update_layout(title_x=0.3,font=dict(size=10))

                            st.plotly_chart(fig4, key=f"group_chart_{list_name}_{d}",
                                            use_container_width=True)

                            st.divider()
        
        ########## step3 Tab ##########

        ########## cbt ##########
        with tab3:

            st.subheader('Step 3')

            col1, col2 = st.columns(2)

            with col1:

                st.subheader('Cognitive Behavioural Therapy')
            
                for c, list_name in enumerate(cbt_combined_summary['variable']
                                            .unique()):
                  
                    if list_name == 'Session_Count':
                        section_title = 'Sessions'
                    elif list_name == 'Num Waiting':
                        section_title = 'Waiting List'

                    if list_name == 'Session_Count':
                        axis_title = 'Sessions'
                    elif list_name == 'Num Waiting':
                        axis_title = 'Patients'

                    cbt_sessions_weekly_type_filtered = step3_cbt_type_melt[
                                        step3_cbt_type_melt["variable"]==list_name]
                    
                    #st.write(cbt_sessions_weekly_type_filtered)
                    
                    cbt_combined_col1_filtered = cbt_combined_summary[
                                        cbt_combined_summary["variable"]==list_name]
                    
                    #st.write(cbt_combined_col1_filtered)
                    
                    if list_name == 'Session_Count':
                        section_title = 'Sessions'

                        custom_colors = {'First': "#2ca02c",
                                        'Follow-Up': "#98df8a"}
                        
                        custom_stack_order = ["First", "Follow-Up"]  # Order from bottom to top
                    
                        fig1 = px.histogram(cbt_sessions_weekly_type_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color='Session Type',
                                            color_discrete_map=custom_colors, #custom_colors,
                                            category_orders={'Session Type': 
                                                            custom_stack_order},
                                            title=f'Number of Sessions per Week')
                        
                        fig1.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig1.update_traces(marker_line_color='black', marker_line_width=1)

                        fig1.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig1, key=f"cbt_chart_{list_name}_{c}"
                                                    ,use_container_width=True)

                        st.divider()

                    elif list_name == 'Num Waiting':
                        section_title = 'Waiting List'

                        # get the average waiting list across all the runs
                        weekly_avg_col1 = cbt_combined_col1_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig2 = px.line(
                                    weekly_avg_col1,
                                    x="Week Number",
                                    #color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Patients'
                                        },
                                    height=425,
                                    width=500,
                                    title='Number of Patients Waiting by Week'
                                    )
                        
                        #fig2.update_traces(line=dict(dash='dot'))

                        fig2.update_layout(showlegend=False)

                        fig2.update_traces(line=dict(width=3, color='blue'))
                                            
                        # get rid of 'variable' prefix resulting from df.melt
                        fig2.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                       
                        fig2.update_layout(title_x=0.3,font=dict(size=10))
                        #fig.

                        st.plotly_chart(fig2, key=f"cbt_chart_{list_name}_{c}"
                                                    ,use_container_width=True)

                        st.divider()

            with col2:            
                              
                if list_name == 'Total_IsDNA':
                    axis_title = 'DNAs'
                elif list_name == 'Avg Wait':
                    axis_title = 'Weeks'

                st.subheader('')

                for d, list_name in enumerate(cbt_combined_summary['variable']
                                            .unique()):

                    cbt_sessions_weekly_type_filtered = step3_cbt_type_melt[
                                        step3_cbt_type_melt["variable"]==list_name]
                    
                    cbt_combined_col2_filtered = cbt_combined_summary[
                                        cbt_combined_summary["variable"]==
                                        list_name]
                    
                    cbt_combined_col2_max = cbt_combined_summary[
                                        cbt_combined_summary["variable"]==
                                        'Max Wait']
                    
                    if list_name == 'Total_IsDNA':

                        custom_colors_red = {
                                            'First': "#d62728", 
                                            'Follow-Up': "#ff9896"
                                            }
                        custom_stack_order_red = ["First", "Follow-Up"] # Order from bottom to top
                        
                        section_title = ''
                    
                        fig3 = px.histogram(cbt_sessions_weekly_type_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color='Session Type',
                                            color_discrete_map=custom_colors_red, #custom_colors,
                                            category_orders={'Session Type': 
                                                            custom_stack_order_red},
                                            title=f'Number of DNAs per Week')
                        
                        fig3.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig3.update_traces(marker_line_color='black', marker_line_width=1)

                        fig3.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig3, key=f"cbt_chart_{list_name}_{d}",
                                                    use_container_width=True)

                        st.divider()

                    elif list_name == 'Avg Wait':

                        section_title = ''

                        # get the average waiting time across all the runs
                        weekly_avg_col2 = cbt_combined_col2_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()

                        fig4 = px.line(
                                    weekly_avg_col2,
                                    x="Week Number",
                                    #color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Weeks'
                                        },
                                    height=425,
                                    width=500,
                                    title='Waiting Time by Week'
                                    )
                        
                        # Force the first trace to appear in the legend
                        fig4.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))
                
                        # get the average waiting time across all the runs
                        weekly_max_col2 = cbt_combined_col2_max.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()

                        fig4.add_trace(
                                    go.Scatter(x=weekly_max_col2["Week Number"],
                                            y=weekly_max_col2["value"], name='Maximum',
                                            line=dict(width=3,color='red')))

                        # add line for 18 week RTT
                        fig4.add_trace(
                                go.Scatter(x=weekly_avg_col2["Week Number"],
                                        y=np.repeat(18,sim_duration_input*2),
                                        name='18 Week RTT',line=dict(width=3,
                                        color='green')))
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig4.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                        
                        fig4.update_layout(title_x=0.3,font=dict(size=10))

                        st.plotly_chart(fig4, key=f"cbt_chart_{list_name}_{d}",
                                        use_container_width=True)

                        st.divider()

            ########## counselling ##########

            col3, col4 = st.columns(2)

            with col3:

                    st.subheader('Depression Counselling')
                
                    for c, list_name in enumerate(couns_combined_summary['variable']
                                                .unique()):
                    
                        if list_name == 'Session_Count':
                            section_title = 'Sessions'
                        elif list_name == 'Num Waiting':
                            section_title = 'Waiting List'

                        if list_name == 'Session_Count':
                            axis_title = 'Sessions'
                        elif list_name == 'Num Waiting':
                            axis_title = 'Patients'

                        couns_sessions_weekly_type_filtered = step3_couns_type_melt[
                                            step3_couns_type_melt["variable"]==list_name]
                        
                        #st.write(couns_sessions_weekly_type_filtered)
                        
                        couns_combined_col3_filtered = couns_combined_summary[
                                            couns_combined_summary["variable"]==list_name]
                        
                        if list_name == 'Session_Count':
                            section_title = 'Sessions'

                            custom_colors = {'First': "#2ca02c",
                                            'Follow-Up': "#98df8a"}
                            
                            custom_stack_order = ["First", "Follow-Up"]  # Order from bottom to top
                        
                            fig1 = px.histogram(couns_sessions_weekly_type_filtered, 
                                                x='Week Number',
                                                y='value',
                                                nbins=sim_duration_input,
                                                labels={'value': 'Sessions'},
                                                color='Session Type',
                                                color_discrete_map=custom_colors, #custom_colors,
                                                category_orders={'Session Type': 
                                                                custom_stack_order},
                                                title=f'Number of Sessions per Week')
                            
                            fig1.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                            
                            fig1.update_traces(marker_line_color='black', marker_line_width=1)

                            fig1.update_yaxes(title_text="Sessions")

                            st.plotly_chart(fig1, key=f"couns_chart_{list_name}_{c}"
                                                        ,use_container_width=True)

                            st.divider()

                        elif list_name == 'Num Waiting':
                            section_title = 'Waiting List'

                            # get the average waiting list across all the runs
                            weekly_avg_col1 = couns_combined_col3_filtered.groupby(['Week Number',
                                                            'variable'])['value'].mean(
                                                            ).reset_index()
                            
                            fig2 = px.line(
                                        weekly_avg_col1,
                                        x="Week Number",
                                        #color="Run Number",
                                        #line_dash="Run",
                                        y="value",
                                        labels={
                                                "value": 'Patients'
                                            },
                                        height=425,
                                        width=500,
                                        title='Number of Patients Waiting by Week'
                                        )
                            
                            #fig2.update_traces(line=dict(dash='dot'))

                            fig2.update_layout(showlegend=False)

                            fig2.update_traces(line=dict(width=3, color='blue'))
                                                
                            # get rid of 'variable' prefix resulting from df.melt
                            fig2.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                    ("=")[1]))
                        
                            fig2.update_layout(title_x=0.3,font=dict(size=10))
                            #fig.

                            st.plotly_chart(fig2, key=f"couns_chart_{list_name}_{c}"
                                                        ,use_container_width=True)

                            st.divider()

            with col4:            
                            
                if list_name == 'Total_IsDNA':
                    axis_title = 'DNAs'
                elif list_name == 'Avg Wait':
                    axis_title = 'Weeks'

                st.subheader('')

                for d, list_name in enumerate(couns_combined_summary['variable']
                                            .unique()):

                    couns_sessions_weekly_type_filtered = step3_couns_type_melt[
                                        step3_couns_type_melt["variable"]==list_name]
                    
                    couns_combined_col4_filtered = couns_combined_summary[
                                        couns_combined_summary["variable"]==
                                        list_name]
                    
                    couns_combined_col4_max = couns_combined_summary[
                                        couns_combined_summary["variable"]==
                                        'Max Wait']
                    
                    if list_name == 'Total_IsDNA':
                        
                        custom_colors_red = {
                                            'First': "#d62728", 
                                            'Follow-Up': "#ff9896"
                                            }
                        custom_stack_order_red = ["First", "Follow-Up"] # Order from bottom to top
                        
                        section_title = ''
                    
                        fig3 = px.histogram(couns_sessions_weekly_type_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color='Session Type',
                                            color_discrete_map=custom_colors_red, #custom_colors,
                                            category_orders={'Session Type': 
                                                            custom_stack_order_red},
                                            title=f'Number of DNAs per Week')
                        
                        fig3.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig3.update_traces(marker_line_color='black', marker_line_width=1)

                        fig3.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig3, key=f"couns_chart_{list_name}_{d}",
                                                    use_container_width=True)

                        st.divider()

                    elif list_name == 'Avg Wait':

                        section_title = ''

                        # get the average waiting time across all the runs
                        weekly_avg_col4 = couns_combined_col4_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()

                        fig4 = px.line(
                                    weekly_avg_col4,
                                    x="Week Number",
                                    #color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Weeks'
                                        },
                                    height=425,
                                    width=500,
                                    title='Waiting Time by Week'
                                    )
                        
                        # Force the first trace to appear in the legend
                        fig4.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))
                                                
                        # get the average waiting time across all the runs
                        weekly_max_col4 = couns_combined_col4_max.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                      
                        fig4.add_trace(
                                    go.Scatter(x=weekly_max_col4["Week Number"],
                                            y=weekly_max_col4["value"], name='Maximum',
                                            line=dict(width=3,color='red')))
                        
                        # add line for 18 week RTT
                        fig4.add_trace(
                                go.Scatter(x=weekly_avg_col2["Week Number"],
                                        y=np.repeat(18,sim_duration_input*2),
                                        name='18 Week RTT',line=dict(width=3,
                                        color='green')))
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig4.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                        
                        fig4.update_layout(title_x=0.3,font=dict(size=10))

                        st.plotly_chart(fig4, key=f"couns_chart_{list_name}_{d}",
                                        use_container_width=True)

                        st.divider()

        ########## RTT Tab ##########
        
        with tab4:

            st.subheader('Referral To Treatment Waiting Times')

            col1, col2 = st.columns(2)

            with col1:

                st.markdown('#### Psych Wellbeing Practitioner - 1:1')

                pwp_rtt_avg = pwp_rtt_summary[pwp_rtt_summary['variable'] == 'Avg RTT']
                pwp_rtt_max = pwp_rtt_summary[pwp_rtt_summary['variable'] == 'Max RTT']

                fig1 = px.line(
                    pwp_rtt_avg,
                    x="Week Number",
                    y="value",
                    labels={"value": "Weeks"},
                    height=425,
                    width=500,
                    title="Referral To Treatment Waits"
                )

                # Force the first trace to appear in the legend
                fig1.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))

                # Add Max RTT trace
                fig1.add_trace(
                    go.Scatter(
                        x=pwp_rtt_max["Week Number"],
                        y=pwp_rtt_max["value"],
                        name='Maximum',
                        line=dict(width=3, color='red')
                    )
                )

                fig1.update_layout(title_x=0.3, font=dict(size=10))

                st.plotly_chart(fig1, key=f"pwp_chart_{list_name}", use_container_width=True)
                st.divider()

                st.markdown('#### Psych Wellbeing Practitioner - Groups')
            
                group_rtt_avg = group_rtt_summary[group_rtt_summary['variable'] == 'Avg RTT']
                group_rtt_max = group_rtt_summary[group_rtt_summary['variable'] == 'Max RTT']

                fig2 = px.line(
                    group_rtt_avg,
                    x="Week Number",
                    y="value",
                    labels={"value": "Weeks"},
                    height=425,
                    width=500,
                    title="Referral To Treatment Waits"
                )

                # Force the first trace to appear in the legend
                fig2.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))

                # Add Max RTT trace
                fig2.add_trace(
                    go.Scatter(
                        x=group_rtt_max["Week Number"],
                        y=group_rtt_max["value"],
                        name='Maximum',
                        line=dict(width=3, color='red')
                    )
                )

                fig2.update_layout(title_x=0.3, font=dict(size=10))

                st.plotly_chart(fig2, key=f"group_chart_{list_name}", use_container_width=True)
                st.divider()

            with col2:

                st.markdown('#### Cognitive Behavioural Therapy')

                cbt_rtt_avg = cbt_rtt_summary[cbt_rtt_summary['variable'] == 'Avg RTT']
                cbt_rtt_max = cbt_rtt_summary[cbt_rtt_summary['variable'] == 'Max RTT']

                fig3 = px.line(
                    cbt_rtt_avg,
                    x="Week Number",
                    y="value",
                    labels={"value": "Weeks"},
                    height=425,
                    width=500,
                    title="Referral To Treatment Waits"
                )

                # Force the first trace to appear in the legend
                fig3.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))

                # Add Max RTT trace
                fig3.add_trace(
                    go.Scatter(
                        x=cbt_rtt_max["Week Number"],
                        y=cbt_rtt_max["value"],
                        name='Maximum',
                        line=dict(width=3, color='red')
                    )
                )

                fig3.update_layout(title_x=0.3, font=dict(size=10))

                st.plotly_chart(fig3, key=f"cbt_chart_{list_name}", use_container_width=True)
                st.divider()

                st.markdown('#### Depression Counselling')
            
                couns_rtt_avg = couns_rtt_summary[couns_rtt_summary['variable'] == 'Avg RTT']
                couns_rtt_max = couns_rtt_summary[couns_rtt_summary['variable'] == 'Max RTT']

                fig4 = px.line(
                    couns_rtt_avg,
                    x="Week Number",
                    y="value",
                    labels={"value": "Weeks"},
                    height=425,
                    width=500,
                    title="Referral To Treatment Waits"
                )

                # Force the first trace to appear in the legend
                fig4.update_traces(name='Average', showlegend=True, line=dict(width=3, color='blue'))

                # Add Max RTT trace
                fig4.add_trace(
                    go.Scatter(
                        x=couns_rtt_max["Week Number"],
                        y=couns_rtt_max["value"],
                        name='Maximum',
                        line=dict(width=3, color='red')
                    )
                )

                fig4.update_layout(title_x=0.3, font=dict(size=10))

                st.plotly_chart(fig4, key=f"couns_chart_{list_name}", use_container_width=True)
                st.divider()
        #
        # ########## Job Plans ##########
        with tab5:
            
            st.subheader('Job Plans')

            custom_colors = {
                            "CPD Hrs": "#1f77b4",       # Muted blue
                            "Huddle Hrs": "#ffcc00",     # Warm golden yellow
                            "Wellbeing Hrs": "#2ca02c",  # Rich green
                            "Break Hrs": "#17becf",      # Brighter cyan
                            "Supervision Hrs": "#34495e",# Deep navy
                            "TA Hrs": "#d62728",         # Strong red
                            "Session Time": "#20c997",   # Soft turquoise
                            "Admin Time": "#e377c2"      # Gentle pink
                        }
            
            category_order={"variable": ["Session Time"
                                         ,"Admin Time"
                                         ,"Referral Screen Hrs"
                                         ,"TA Hrs"
                                         , "Break Hrs"
                                         , "Wellbeing Hrs"
                                         ,"Supervision Hrs"
                                         ,"Huddle Hrs"
                                         ,"CPD Hrs"]}

            ##### pwp Practitioner #####

            st.markdown('### Psychological Wellbeing Practitioners')

            fig17 = px.histogram(pwp_hours_weekly_summary, 
                                x='Week Number',
                                y='value',
                                nbins=sim_duration_input,
                                labels={'value': 'Hours'
                                        ,'variable':'Time Alloc'},
                                color='variable',
                                color_discrete_map=custom_colors,
                                category_orders=category_order,
                                title=f'Psychological Wellbeing Practitioner Hours by Week')
            
            fig17.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig17.update_traces(marker_line_color='black', marker_line_width=1)

            fig17.update_yaxes(title_text="Hours")

            # add line for available pwp hours
            fig17.add_trace(
                                go.Scatter(x=pwp_hours_weekly_summary["Week Number"],
                                        y=np.repeat(total_pwp_hours,sim_duration_input*2),
                                        name='Total Hrs',line=dict(width=3,
                                        color='green')))
            
            fig17.add_trace(
                                go.Scatter(x=pwp_hours_weekly_summary["Week Number"],
                                        y=np.repeat(clin_pwp_hours,sim_duration_input*2),
                                        name='Clin Hrs',line=dict(width=3,
                                        color='blue')))

            st.plotly_chart(fig17, use_container_width=True)

            st.divider() 

            ##### cbt Practitioner #####

            st.markdown('### Cognitive Behavioural Therapists')

            fig18 = px.histogram(cbt_hours_weekly_summary, 
                                x='Week Number',
                                y='value',
                                nbins=sim_duration_input,
                                labels={'value': 'Hours'
                                        ,'variable':'Time Alloc'},
                                color='variable',
                                color_discrete_map=custom_colors,
                                category_orders=category_order,
                                title=f'Cognitive Behavioural Therapist Hours by Week')
            
            fig18.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig18.update_traces(marker_line_color='black', marker_line_width=1)
            
            fig18.update_yaxes(title_text="Hours")

            # add line for available pwp hours
            fig18.add_trace(
                                go.Scatter(x=cbt_hours_weekly_summary["Week Number"],
                                        y=np.repeat(total_cbt_hours,sim_duration_input*2),
                                        name='Total Hrs',line=dict(width=3,
                                        color='green')))
            
            fig18.add_trace(
                                go.Scatter(x=cbt_hours_weekly_summary["Week Number"],
                                        y=np.repeat(clin_cbt_hours,sim_duration_input*2),
                                        name='Clin Hrs',line=dict(width=3,
                                        color='blue')))

            st.plotly_chart(fig18, use_container_width=True)

            st.divider()   

            ##### couns Practitioner #####

            st.markdown('### Depression Counselling Therapists')

            fig19 = px.histogram(couns_hours_weekly_summary, 
                                x='Week Number',
                                y='value',
                                nbins=sim_duration_input,
                                labels={'value': 'Hours'
                                        ,'variable':'Time Alloc'},
                                color='variable',
                                color_discrete_map=custom_colors,
                                category_orders=category_order,
                                title=f'Depression Counselling Therapist Hours by Week')
            
            fig19.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig19.update_traces(marker_line_color='black', marker_line_width=1)

            fig19.update_yaxes(title_text="Hours")

            # add line for available pwp hours
            fig19.add_trace(
                                go.Scatter(x=couns_hours_weekly_summary["Week Number"],
                                        y=np.repeat(total_couns_hours,sim_duration_input*2),
                                        name='Total Hrs',line=dict(width=3,
                                        color='green')))
            
            fig19.add_trace(
                                go.Scatter(x=couns_hours_weekly_summary["Week Number"],
                                        y=np.repeat(clin_couns_hours,sim_duration_input*2),
                                        name='Clin Hrs',line=dict(width=3,
                                        color='blue')))

            st.plotly_chart(fig19, use_container_width=True)

            st.divider()

        ########## Caseloads ##########
        with tab6:

            st.subheader('Caseloads')

            ##### pwp Practitioner #####

            st.markdown('### Psychological Wellbeing Practitioners')

            fig22 = px.histogram(pwp_caseload_weekly_summary, 
                                x='Week Number',
                                y='caseload_used',
                                nbins=sim_duration_input,
                                labels={'caseload_used': 'Caseload'
                                        #,'caseload_id':'caseload_id'
                                        },
                                #color='caseload_id',
                                color_discrete_sequence=['red'],
                                title=f'Psychological Wellbeing Practitioner Caseload by Week')
            
            fig22.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,
                                legend_traceorder="reversed")
            
            fig22.update_traces(marker_line_color='black', marker_line_width=1)

            fig22.update_yaxes(title_text="Caseload")

             # add line for maximum couns slots
            # Ensure x and y are the same length
            weeks = pwp_caseload_weekly_summary["Week Number"]
            max_value = pwp_caseload_max * (pwp_avail_input + pwp_add_input)

            fig22.add_trace(
                go.Scatter(
                    x=weeks,
                    y=np.full(len(weeks), max_value),  # same length as weeks
                    name='Maximum Slots',
                    line=dict(width=3, color='green')
                )
            )

            st.plotly_chart(fig22, use_container_width=True)

            st.divider()

            ##### cbt Practitioner #####

            st.markdown('### Cognitive Behavioural Therapists')

            fig22 = px.histogram(cbt_caseload_weekly_summary, 
                                x='Week Number',
                                y='caseload_used',
                                nbins=sim_duration_input,
                                labels={'caseload_used': 'Caseload'
                                        #,'caseload_id':'caseload_id'
                                        },
                                #color='caseload_id',
                                color_discrete_sequence=['red'],
                                title=f'Cognitive Behavioural Therapist Caseload by Week')
            
            fig22.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig22.update_traces(marker_line_color='black', marker_line_width=1)

            fig22.update_yaxes(title_text="Caseload")

            # add line for maximum cbt slots
            # Ensure x and y are the same length
            weeks = cbt_caseload_weekly_summary["Week Number"]
            max_value = cbt_caseload_max * (cbt_avail_input + cbt_add_input)

            fig22.add_trace(
                go.Scatter(
                    x=weeks,
                    y=np.full(len(weeks), max_value),  # same length as weeks
                    name='Maximum Slots',
                    line=dict(width=3, color='green')
                )
            )

            st.plotly_chart(fig22, use_container_width=True)

            st.divider()

            ##### couns Practitioner #####

            st.markdown('### Depression Counsellors')

            fig22 = px.histogram(couns_caseload_weekly_summary, 
                                x='Week Number',
                                y='caseload_used',
                                nbins=sim_duration_input,
                                labels={'caseload_used': 'Caseload'
                                        #,'caseload_id':'caseload_id'
                                        },
                                #color='caseload_id',
                                color_discrete_sequence=['red'],
                                title=f'Depression Counsellors Caseload by Week')
            
            fig22.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig22.update_traces(marker_line_color='black', marker_line_width=1)

            fig22.update_yaxes(title_text="Caseload")

            # add line for maximum couns slots
            # Ensure x and y are the same length
            weeks = couns_caseload_weekly_summary["Week Number"]
            max_value = couns_caseload_max * (couns_avail_input + couns_add_input)

            fig22.add_trace(
                go.Scatter(
                    x=weeks,
                    y=np.full(len(weeks), max_value),  # same length as weeks
                    name='Maximum Slots',
                    line=dict(width=3, color='green')
                )
            )

            st.plotly_chart(fig22, use_container_width=True)

            st.divider()   

            