import simpy
import random
import numpy as np
import pandas as pd
import streamlit as st
#import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from iapt_classes import g, Trial
#from app_style import global_page_style

########## Streamlit App ##########

st.set_page_config(layout="wide")

@st.cache_data
def load_referral_rates(): # thanks to Sammi Rosser :-)
    return pd.read_csv("https://raw.githubusercontent.com/MightyAtom220474/IAPT-Pathway-DES/refs/heads/main/.streamlit/talking_therapies_referral_rates.csv",index_col=0)  # Ensure the file is in the app directory

#st.write(load_referral_rates())

#st.logo("https://lancsvp.org.uk/wp-content/uploads/2021/08/nhs-logo-300x189.png")

# Import custom css for using a Google font
# with open("style.css") as css:
#    st.markdown(f'<style>{css.read()}</style>', unsafe_allow_html=True)

#global_page_style('static/css/style.css')

st.title("Talking Therapies Pathway Simulation")

with st.sidebar:

    st.subheader("Model Inputs")

    with st.expander("Screening & Assessment"):

        # Referral Inputs
        st.markdown("#### Screening")
        referral_input = st.slider("Average Number of Referrals Per Week", 0, 1500, g.mean_referrals_pw)
        referral_reject_input = st.number_input("Referral Rejection Rate (%)",
                        min_value=0.0, max_value=20.0, step=0.25, value=4.25)
        referral_review_input = st.number_input("% of Referral sent for Review",
                        min_value=0.0, max_value=50.0, step=0.25, value=40.0)
        referral_screen_input = st.slider("Number of Mins to Screen Referral",
                                          1, 20, 25)
        opt_in_input = st.number_input("% of Referrals that Opt-in",
                        min_value=50.0, max_value=100.0, step=0.5, value=75.0)
        st.markdown("#### Assessment")
        ta_accept_input = st.number_input("% of TA's that are Accepted",
                        min_value=50.0, max_value=100.0, step=0.5, value=70.0)
        ta_time_input = st.slider("Number of Mins to Perform TA", 1, 90, 60)
        step2_step3_rate_input = st.number_input("% of Patients Assigned to Step 2 vs Step 3",
                        min_value=50.0, max_value=100.0, step=0.5, value=85.0)
           
    with st.expander("Step 2"):
        
        # Triage Inputs
        st.divider()
        st.markdown("#### Step 2")
        
        step2_path_ratio = st.number_input("% of Step 2 Allocated to PwP vs Group",
                                           min_value=0.0, max_value=100.0, 
                                           step=1.0, value=85.0)
        step2_first_input = st.slider("Number of Mins for First PwP Appointment",
                                            1, 60, 45)
        step2_fup_input = st.slider("Number of Mins for Follow-up PwP Appointment",
                                    1, 60, 30)
        step2_admin_input = st.slider("Number of Mins for Writing up Step2 Appointment",
                                    1, 20, 15)
        step_up_input = st.number_input("% of Patients Stepped Up", 
                                        min_value=0.0, max_value=10.0,
                                        step=0.25, value=1.0)
        step2_pwp_dna_input = st.number_input("% DNA's for PwP Appointments",
                                            min_value=0.0, max_value=30.0,
                                            step=0.5, value=15.0)
        step2_group_dna_input = st.number_input("% DNA's for Group Sessions",
                                               min_value=0.0, max_value=30.0,
                                               step=0.25, value=22.0)
        step2_group_sessions_input = st.slider("Number of Step2 Group Sessions",
                                              1, 10, 7)
        step2_group_size_input = st.slider("Maximum Step2 Group Size", 1, 12, 7)
        step2_group_duration_input = st.number_input("Length of Group Sessions (mins)",
                                                min_value=180, max_value=300,
                                                step=30, value=240)

    with st.expander("Step 3"):
        
        # Triage Inputs
        st.divider()
        st.markdown("#### Step 3")
        
        step3_path_ratio = st.number_input("% of Step 3 Allocated to Couns vs CBT",
                                           min_value=0.0, max_value=100.0,
                                           step=0.5, value=37.0)
        step_down_input = st.number_input("% of Patients Stepped Down",
                                          min_value=0.0, max_value=20.0,
                                          step=0.5, value=12.0)
        step3_cbt_first_input = st.slider("Number of Mins for First CBT Appointment",
                                          1, 60, 45)
        step3_cbt_fup_input = st.slider("Number of Mins for Follow-up CBT Appointment",
                                        1, 60, 30)
        step3_cbt_dna_input = st.number_input("% DNA's for CBT Appointments",
                                              min_value=0.0, max_value=30.0,
                                              step=0.5, value=20.0)
        step3_couns_first_input = st.slider("Number of Mins for First Couns Appointment",
                                            1, 60, 45)
        step3_couns_fup_input = st.slider("Number of Mins for Follow-up Couns Appointment",
                                          1, 60, 30)
        step3_admin_input = st.slider("Number of Mins for Writing up Step3 Appointment",
                                    1, 20, 15)
        step3_couns_dna_input = st.number_input("% DNA's for Counselling Sessions",
                                                min_value=0.0, max_value=30.0,
                                                step=0.25, value=20.0)
        step3_session_var_input = st.number_input("% of Instances where Patients Receive Additional Sessions ",
                                                  min_value=0.0, max_value=30.0,
                                                  step=0.25, value=20.0)
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
                                          step=1,value = g.number_staff_cbt)
        couns_avail_input = st.number_input(label="Starting Number of DepC Practitioners WTE",
                                            min_value=1,max_value=100,
                                            step=1,value = g.number_staff_couns)
        pwp_avail_input = st.number_input(label="Starting Number of PwP Practitioners WTE",
                                          min_value=1,max_value=200,
                                          step=1,value = g.number_staff_pwp)
        cbt_add_input = st.number_input("Additional Number of CBT Practitioners WTE",
                        min_value=-20, max_value=20, step=1, value=0)
        couns_add_input = st.number_input("Additional Number of DepC Practitioners WTE",
                        min_value=-10, max_value=20, step=1, value=0)
        pwp_add_input = st.number_input("Additional Number of PwP Practitioners WTE",
                        min_value=-25, max_value=25, step=1, value=0)
        cbt_caseload_input = st.slider("Number of Patients Allowed on CBT Caseload",
                                            1, 50, g.cbt_caseload)
        couns_caseload_input = st.slider("Number of Patients Allowed on DepC Caseload",
                                            1, 50, g.couns_caseload)
        pwp_caseload_input = st.slider("Number of Patients Allowed on PwP Caseload",
                                            1, 50, g.pwp_caseload)
        cbt_hours_avail_input = st.number_input(label="Non-Clinical Hours p/w for CBT Pratitioners",
                                                min_value=10.0,max_value=25.0,
                                                step=0.5,value = g.hours_avail_cbt)
        couns_hours_avail_input = st.number_input(label="Non-Clinical Hours p/w for Counselling Pratitioners",
                                                  min_value=10.0,max_value=25.0,
                                                  step=0.5,value = g.hours_avail_couns)
        pwp_hours_avail_input = st.number_input(label="Non-Clinical Hours p/w for PwP Pratitioners",
                                                min_value=10.0,max_value=25.0,
                                                step=0.5,value = g.hours_avail_pwp)
        weeks_lost_input = st.number_input("Weeks Lost to Leave/Sickness etc.",
                            min_value=0.0, max_value=20.0, step=0.25, value=10.0)
            
    with st.expander("Simulation Parameters"):
    
        st.divider()
        st.markdown("#### Simulation Parameters")
        sim_duration_input =  st.slider("Simulation Duration (weeks)",
                                        min_value=26, max_value=520,
                                        value=52, step=26)
        st.write(f"The service is running for {sim_duration_input} weeks")
        number_of_runs_input = st.slider("Number of Simulation Runs", 1, 20, 2)
        #st.toggle(label='Test Run?', value=False)

g.referral_rate_lookup = load_referral_rates()

##### Screening
g.mean_referrals_pw = referral_input
#g.base_waiting_list = 2741
g.referral_rejection_rate = referral_reject_input/100
g.referral_review_rate = referral_review_input
g.referral_screen_time = referral_screen_input
g.opt_in_rate = opt_in_input/100
g.ta_accept_rate = ta_accept_input/100
g.step2_step3_ratio = (step2_step3_rate_input/100,1-(step2_step3_rate_input/100))

##### Step 2
g.step2_path_ratios = (step2_path_ratio/100,1-(step2_path_ratio/100))
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
g.step3_cbt_1st_mins = step2_first_input
g.step3_cbt_fup_mins = step2_fup_input
g.step3_cbt_dna_rate = step3_cbt_dna_input/100
g.step3_couns_1st_mins = step2_first_input
g.step3_couns_fup_mins = step2_fup_input
g.step3_couns_dna_rate = step3_couns_dna_input/100
g.step_down_rate = step_down_input/100
g.step3_session_admin = step3_admin_input

##### Job Plans
g.cbt_avail = cbt_avail_input + cbt_add_input
g.couns_avail = couns_avail_input + couns_add_input
g.pwp_avail = pwp_avail_input + pwp_add_input
g.cbt_caseload = cbt_caseload_input
g.couns_caseload = couns_caseload_input
g.pwp_caseload = pwp_caseload_input
# calculate total hours for job plans
total_cbt_hours = g.cbt_avail*37.5
total_couns_hours = g.couns_avail*37.5
total_pwp_hours = g.pwp_avail*37.5

g.sim_duration = sim_duration_input
g.number_of_runs = number_of_runs_input

###########################################################
# Run a trial using the parameters from the g class and   #
# print the results                                       #
###########################################################

button_run_pressed = st.button("Run simulation")

if button_run_pressed:
    with st.spinner('Simulating the system...'):

# Create an instance of the Trial class
        my_trial = Trial()
        pd.set_option('display.max_rows', 1000)
        # Call the run_trial method of our Trial class object
        step2_results_df, step2_sessions_df, step3_results_df, step3_sessions_df, asst_weekly_dfs, step2_waiting_dfs, step3_waiting_dfs, staff_weekly_dfs, caseload_weekly_dfs = my_trial.run_trial()
        

        st.subheader(f'Summary of all {g.number_of_runs} Simulation Runs over {g.sim_duration}'
                     f' Weeks with {cbt_add_input} additional CBT,'
                      f' {couns_add_input} additional Depression Counsellors and '
                      f'{pwp_add_input} additional PwP Practitioners')
        
        ##### get all data structured correctly #####
                
        # turn asst values from running total to weekly total
        #asst_weekly_dfs['Referrals Recvd'] = (asst_weekly_dfs['Referrals Received']-asst_weekly_dfs['Referrals Received'].shift(1))
        asst_weekly_dfs['Referral Screen Hrs'] = (asst_weekly_dfs['Referral Screen Mins']-asst_weekly_dfs['Referral Screen Mins'].shift(1))/60
        asst_weekly_dfs['Rejected Referrals'] = (asst_weekly_dfs['Referrals Rejected']-asst_weekly_dfs['Referrals Rejected'].shift(1))
        asst_weekly_dfs['Referral Reviews'] = asst_weekly_dfs['Referrals Reviewed']#-asst_weekly_dfs['Referrals Reviewed'].shift(1))
        asst_weekly_dfs['Reviewed Rejected'] = asst_weekly_dfs['Reviews Rejected']#-asst_weekly_dfs['Reviews Rejected'].shift(1))
        asst_weekly_dfs['Optin Total'] = (asst_weekly_dfs['Referrals Opted-in']-asst_weekly_dfs['Referrals Opted-in'].shift(1))
        #asst_weekly_dfs['TA Waiting List'] = (asst_weekly_dfs['TA Waiting List']-asst_weekly_dfs['TA Waiting List'].shift(1))
        asst_weekly_dfs['TA Accept'] = (asst_weekly_dfs['TA Total Accept']-asst_weekly_dfs['TA Total Accept'].shift(1))
        asst_weekly_dfs['TA Hrs'] = (asst_weekly_dfs['TA Mins']-asst_weekly_dfs['TA Mins'].shift(1))/60

        # get rid of negative values
        num = asst_weekly_dfs._get_numeric_data()

        num[num < 0] = 0

        asst_weekly_dfs['Accepted Referrals'] = asst_weekly_dfs['Referrals Received']-asst_weekly_dfs['Rejected Referrals']
        
        # filter dataframe to just return columns needed
        asst_weekly_summary = asst_weekly_dfs[['Run Number','Week Number','Referrals Received','Referral Screen Hrs','Accepted Referrals','Rejected Referrals','Referral Reviews','Reviewed Rejected','Optin Total','TA Waiting List','TA Avg Wait','TA Accept','TA Hrs']]
               
        asst_weekly_summary = asst_weekly_summary[asst_weekly_summary["Week Number"] != 0]
                              
        step2_pwp_results_summary = step2_results_df.loc[step2_results_df[
                'Route Name'] == 'PwP', ['Run Number', 'Week Number', 
                                      'WL Posn','Q Time',
                                      'IsStep','IsDropout']]

        step2_pwp_sessions_summary = step2_sessions_df.loc[step2_sessions_df[
                'Route Name'] == 'PwP', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']]
        
        step2_group_results_summary = step2_results_df.loc[step2_results_df[
                'Route Name'] == 'Group', ['Run Number', 'Week Number', 
                                      'WL Posn','Q Time',
                                      'IsStep','IsDropout']]
        
        step2_group_sessions_summary = step2_sessions_df.loc[step2_sessions_df[
                'Route Name'] == 'Group', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']]
        
        step3_cbt_results_summary = step3_results_df.loc[step3_results_df[
                'Route Name'] == 'CBT', ['Run Number', 'Week Number', 
                                      'WL Posn','Q Time',
                                      'IsStep','IsDropout']]
        
        step3_cbt_sessions_summary = step3_sessions_df.loc[step3_sessions_df[
                'Route Name'] == 'CBT', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']]
        
        step3_couns_results_summary = step3_results_df.loc[step3_results_df[
                'Route Name'] == 'Couns', ['Run Number', 'Week Number', 
                                      'WL Posn','Q Time',
                                      'IsStep','IsDropout']]
        
        step3_couns_sessions_summary = step3_sessions_df.loc[step3_sessions_df[
                'Route Name'] == 'Couns', ['Run Number', 'Week Number', 
                                      'Session Number','Session Time',
                                      'Admin Time','IsDNA']]
        
        # Define correct aggregation mapping based on the variable name
        aggregated_sessions = {}
        
        agg_mapping = {
            'Session Number': 'count',
            'Session Time': 'sum',
            'Admin Time': 'sum',
            'IsDNA': 'sum'
        }

        # Dictionary of DataFrames to process
        aggregated_sessions_dfs = {
            'step2_pwp_sessions_summary': step2_pwp_sessions_summary,
            'step2_group_sessions_summary': step2_group_sessions_summary,
            'step3_cbt_sessions_summary': step3_cbt_sessions_summary,
            'step3_couns_sessions_summary': step3_couns_sessions_summary
        }

        

        for name, df in aggregated_sessions_dfs.items():
            # Melt the DataFrame
            melted_df = pd.melt(df, id_vars=['Run Number', 'Week Number'], var_name='variable', value_name='value')
            #st.write(melted_df)
            # Debug: Check melted output
            # print(f"Checking {name} melted_df:")
            # print(melted_df.head())

            # Apply the aggregation function based on variable
            aggregated_sessions_df = melted_df.groupby(['Run Number', 'Week Number', 'variable'])['value'].agg(
                lambda x: x.sum() if agg_mapping.get(x.name, 'sum') == 'sum' else x.count()
            ).reset_index()

            # Store the result
            aggregated_sessions[name] = aggregated_sessions_df
 
        ########## repeat above but for results dfs ##########
        # Define correct aggregation mapping based on the variable name
        agg_mapping = {
            'WL Posn': 'max',
            'Q Time': 'mean',
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
            melted_df = pd.melt(df, id_vars=['Run Number', 'Week Number'], var_name='variable', value_name='value')
            
            # Debug: Check melted output
            # print(f"Checking {name} melted_df:")
            # print(melted_df.head())

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
            aggregated_results_df = melted_df.groupby(['Run Number', 'Week Number', 'variable']).agg(
                {'value': agg_func}
            ).reset_index()

            # Store the result
            aggregated_results[name] = aggregated_results_df

        # Extract final DataFrames

        pwp_sessions_summary = aggregated_sessions['step2_pwp_sessions_summary']
        group_sessions_summary = aggregated_sessions['step2_group_sessions_summary']
        cbt_sessions_summary = aggregated_sessions['step3_cbt_sessions_summary']
        couns_sessions_summary = aggregated_sessions['step3_couns_sessions_summary']

        pwp_results_summary = aggregated_results['step2_pwp_results_summary']
        group_results_summary = aggregated_results['step2_group_results_summary']
        cbt_results_summary = aggregated_results['step3_cbt_results_summary']
        couns_results_summary = aggregated_results['step3_couns_results_summary']
 
        ##### merge results and sessions #####
        pwp_combined_summary = pd.concat([pwp_sessions_summary,pwp_results_summary], ignore_index=True)
        group_combined_summary = pd.concat([group_sessions_summary,group_results_summary], ignore_index=True)
        cbt_combined_summary = pd.concat([cbt_sessions_summary,cbt_results_summary], ignore_index=True)
        couns_combined_summary = pd.concat([couns_sessions_summary,couns_results_summary], ignore_index=True)
        # get rid of any sessions recorded beyond the simulation period
        pwp_combined_summary = pwp_combined_summary[pwp_combined_summary["Week Number"] <= sim_duration_input]
        group_combined_summary = group_combined_summary[group_combined_summary["Week Number"] <= sim_duration_input]
        cbt_combined_summary = cbt_combined_summary[cbt_combined_summary["Week Number"] <= sim_duration_input]
        couns_combined_summary = couns_combined_summary[couns_combined_summary["Week Number"] <= sim_duration_input]
        # get rid of week zero as no sessions run until week 1 when assessments come through
        pwp_combined_summary = pwp_combined_summary[pwp_combined_summary["Week Number"] != 0]
        group_combined_summary = group_combined_summary[group_combined_summary["Week Number"] != 0]
        cbt_combined_summary = cbt_combined_summary[cbt_combined_summary["Week Number"] != 0]
        couns_combined_summary = couns_combined_summary[couns_combined_summary["Week Number"] != 0]
        
        ##### Staff Non-clinical Activity #####
        # turn into hours and divide by number of sim runs to get average across all the runs
        staff_weekly_dfs['Supervision Hrs'] = staff_weekly_dfs['Supervision Mins']/(60*number_of_runs_input)
        staff_weekly_dfs['Break Hrs'] = staff_weekly_dfs['Break Mins']/(60*number_of_runs_input)
        staff_weekly_dfs['Wellbeing Hrs'] = staff_weekly_dfs['Wellbeing Mins']/(60*number_of_runs_input)
        staff_weekly_dfs['Huddle Hrs'] = staff_weekly_dfs['Huddle Mins']/(60*number_of_runs_input)
        staff_weekly_dfs['CPD Hrs'] = staff_weekly_dfs['CPD Mins']/(60*number_of_runs_input)
        
        pwp_weekly_act_dfs = staff_weekly_dfs.loc[staff_weekly_dfs[
                'Job Role'] == 'PwP']
        
        pwp_weekly_activity = pd.melt(pwp_weekly_act_dfs, value_vars=['Supervision Hrs',
                                                                 'Break Hrs',
                                                                 'Wellbeing Hrs',
                                                                 'Huddle Hrs',
                                                                 'CPD Hrs'],
                                                                 id_vars=[
                                                                'Week Number'])
        
        cbt_weekly_act_dfs = staff_weekly_dfs.loc[staff_weekly_dfs[
                'Job Role'] == 'CBT']
        
        cbt_weekly_activity = pd.melt(cbt_weekly_act_dfs, value_vars=['Supervision Hrs',
                                                                 'Break Hrs',
                                                                 'Wellbeing Hrs',
                                                                 'Huddle Hrs',
                                                                 'CPD Hrs'],
                                                                 id_vars=[
                                                                'Week Number'])
        couns_weekly_act_dfs = staff_weekly_dfs.loc[staff_weekly_dfs[
                'Job Role'] == 'Couns']
        
        couns_weekly_activity = pd.melt(couns_weekly_act_dfs, value_vars=['Supervision Hrs',
                                                                 'Break Hrs',
                                                                 'Wellbeing Hrs',
                                                                 'Huddle Hrs',
                                                                 'CPD Hrs'],
                                                                 id_vars=[
                                                                'Week Number'])
        
        # st.write(pwp_sessions_summary)
        # st.write(group_sessions_summary)
        # st.write(cbt_sessions_summary)
        # st.write(couns_sessions_summary)

        # st.write(pwp_results_summary)
        # st.write(group_results_summary)
        # st.write(cbt_results_summary)
        # st.write(couns_results_summary)

        # st.write(step2_sessions_summary)
        # st.write(step3_sessions_summary)
   
        with st.expander("See explanation"):
            st.write('This Simulation is designed to replicate the flow '
                     'of patients through the Talking Therapies Assessment and'
                     'Treatment Pathway.')
  
          
        ########## Job Plans Tab ##########
        ##### PwP Practitoner #####
        
        # get time values from sessions dataframe and convert to hours - divide by 60 * sim duration to get average across all runs when summed up
        # PwP
        pwp_sessions_weekly_summary = pwp_sessions_summary[pwp_sessions_summary['variable'].isin(['Session Time','Admin Time'])]
        pwp_sessions_weekly_summary.drop('Run Number', axis=1)
        pwp_sessions_weekly_summary[pwp_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])] = \
                pwp_sessions_weekly_summary[pwp_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])].div(60*number_of_runs_input).round()
        # Group
        group_sessions_weekly_summary = group_sessions_summary[group_sessions_summary['variable'].isin(['Session Time','Admin Time'])]
        group_sessions_weekly_summary[group_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])] = \
                group_sessions_weekly_summary[group_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])].div(60*number_of_runs_input).round()
        # CBT
        cbt_sessions_weekly_summary = cbt_sessions_summary[cbt_sessions_summary['variable'].isin(['Session Time','Admin Time'])]
        cbt_sessions_weekly_summary[cbt_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])] = \
                cbt_sessions_weekly_summary[cbt_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])].div(60*number_of_runs_input).round()
        # Couns
        couns_sessions_weekly_summary = couns_sessions_summary[couns_sessions_summary['variable'].isin(['Session Time','Admin Time'])]
        couns_sessions_weekly_summary[couns_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])] = \
                couns_sessions_weekly_summary[couns_sessions_weekly_summary.select_dtypes(include="number").columns.difference(["Week Number"])].div(60*number_of_runs_input).round()
              
        
        
        # pwp_sessions_weekly_summary['variable'] = pwp_sessions_weekly_summary['variable'].replace({"Session Hrs": "PwP Sessions", "Admin Hrs": "PwP Admin"}, inplace=True)
        # group_sessions_weekly_summary['variable'] = group_sessions_weekly_summary['variable'].replace({"Session Hrs": "Group Sessions", "Admin Hrs": "Group Admin"}, inplace=True)
        # combine PwP and Group as all delivered by PwP
        pwp_group_sessions_combined = pd.concat([pwp_sessions_weekly_summary,group_sessions_weekly_summary], ignore_index=True)
        
        # get time value from asst dataframe
        pwp_asst_weekly_summary = asst_weekly_dfs[['Week Number','Referral Screen Hrs','TA Hrs']]
        # get average across all runs
        pwp_asst_weekly_summary[['Referral Screen Hrs','TA Hrs']] = pwp_asst_weekly_summary[['Referral Screen Hrs','TA Hrs']]/number_of_runs_input
        pwp_asst_weekly_summary[['Referral Screen Hrs','TA Hrs']] = pwp_asst_weekly_summary[['Referral Screen Hrs','TA Hrs']]*0.87 # 87% of TA's done by PwP

        pwp_asst_weekly_summary = pd.melt(pwp_asst_weekly_summary, value_vars=['Referral Screen Hrs',
                                                                 'TA Hrs'],
                                                                 id_vars=[
                                                                'Week Number'])

        ##### CBT #####

        cbt_asst_weekly_summary = asst_weekly_dfs[['Week Number','TA Hrs']]
        # get average across all runs
        cbt_asst_weekly_summary['TA Hrs'] = asst_weekly_dfs['TA Hrs']/number_of_runs_input
        cbt_asst_weekly_summary['TA Hrs'] = cbt_asst_weekly_summary['TA Hrs']*0.11 # 11% of TA's done by CBT

        cbt_asst_weekly_summary = pd.melt(cbt_asst_weekly_summary, value_vars=[
                                                                 'TA Hrs'],
                                                                 id_vars=[
                                                                'Week Number'])
        ##### CBT #####

        couns_asst_weekly_summary = asst_weekly_dfs[['Week Number','TA Hrs']]
        couns_asst_weekly_summary['TA Hrs'] = couns_asst_weekly_summary['TA Hrs']/number_of_runs_input
        couns_asst_weekly_summary['TA Hrs'] = couns_asst_weekly_summary['TA Hrs']*0.02 # 2% of TA's done by Couns

        couns_asst_weekly_summary = pd.melt(couns_asst_weekly_summary, value_vars=[
                                                                 'TA Hrs'],
                                                                 id_vars=[
                                                                'Week Number'])
      
        ##### bring all the clinical and non-clinical activity data together
        pwp_hours_weekly_summary = pd.concat([pwp_sessions_weekly_summary,pwp_asst_weekly_summary,pwp_weekly_activity], ignore_index=True)
        # get rid of sessions that go beyond sim duration
        pwp_hours_weekly_summary = pwp_hours_weekly_summary[pwp_hours_weekly_summary["Week Number"] <=sim_duration_input]
           
        cbt_hours_weekly_summary = pd.concat([cbt_sessions_weekly_summary,cbt_asst_weekly_summary,cbt_weekly_activity], ignore_index=True)
        # get rid of sessions that go beyond sim duration
        cbt_hours_weekly_summary = cbt_hours_weekly_summary[cbt_hours_weekly_summary["Week Number"] <=sim_duration_input]

        couns_hours_weekly_summary = pd.concat([couns_sessions_weekly_summary,couns_asst_weekly_summary,couns_weekly_activity], ignore_index=True)
        # get rid of sessions that go beyond sim duration
        couns_hours_weekly_summary = couns_hours_weekly_summary[couns_hours_weekly_summary["Week Number"] <=sim_duration_input]
        
        
        ## Structure data for plotting in dashboard ##
        ########## Referrals & Assessments ##########

        asst_referrals_col1_unpivot = pd.melt(asst_weekly_summary, value_vars=['Referrals Received',
                                                                 'TA Avg Wait'],
                                                                 id_vars=['Run Number',
                                                                'Week Number'])
        
        asst_referrals_col2_unpivot = pd.melt(asst_weekly_summary, value_vars=['Rejected Referrals',
                                                                 'TA Waiting List'],
                                                                 id_vars=['Run Number',
                                                                'Week Number'])
        
        asst_referrals_col3_unpivot = pd.melt(asst_weekly_summary, value_vars=['Accepted Referrals',
                                                                 'TA Accept'],
                                                                 id_vars=['Run Number',
                                                                'Week Number'])
        ###########################
        ## Dashboard Starts Here ##
        ###########################
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["Referral & Assessment", "Step 2","Step 3","Job Plans","Caseloads"])
        
        # ########## Referral & Assessment Tab ##########
        
        with tab1:    

            col1, col2, col3 = st.columns(3)

            with col1:
            
                for i, list_name in enumerate(asst_referrals_col1_unpivot['variable']
                                            .unique()):

                    if list_name == 'Referrals Received':
                        section_title = 'Referrals'
                    elif list_name == 'TA Avg Wait':
                        section_title = 'Assessment'

                    if list_name == 'Referrals Received':
                        axis_title = 'Referrals'
                    elif list_name == 'TA Avg Wait':
                        axis_title = 'Weeks'

                    st.subheader(section_title)

                    asst_referrals_col1_filtered = asst_referrals_col1_unpivot[
                                        asst_referrals_col1_unpivot["variable"]==list_name]
                    
                    fig = px.line(
                                asst_referrals_col1_filtered,
                                x="Week Number",
                                color="Run Number",
                                #line_dash="Run",
                                y="value",
                                labels={
                                        "value": axis_title
                                       },
                                height=500,
                                width=350,
                                title=f'{list_name} by Week'
                                )
                    
                    fig.update_traces(line=dict(dash='dot'))
                    
                    # get the average waiting list across all the runs
                    weekly_avg_col1 = asst_referrals_col1_filtered.groupby(['Week Number',
                                                    'variable'])['value'].mean(
                                                    ).reset_index()
                    
                    fig.add_trace(
                                go.Scatter(x=weekly_avg_col1["Week Number"],
                                        y=weekly_avg_col1["value"], name='Average',
                                        line=dict(width=3,color='blue')))
        
                    
                    # get rid of 'variable' prefix resulting from df.melt
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                            ("=")[1]))
                    #fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[1]))

                    # fig.update_layout(
                    #     title=dict(text=f'ADHD {'variable'} Waiting Lists by Week, 
                    #               font=dict(size=20), automargin=True, yref='paper')
                    #     ))
                    fig.update_layout(title_x=0.3,font=dict(size=10))
                    #fig.

                    st.plotly_chart(fig, use_container_width=True)

                    st.divider()

            with col2:
                           
                for i, list_name in enumerate(asst_referrals_col2_unpivot['variable']
                                            .unique()):

                    asst_referrals_col2_filtered = asst_referrals_col2_unpivot[
                                        asst_referrals_col2_unpivot["variable"]==list_name]
                    
                    if list_name == 'Rejected Referrals':
                        axis_title = 'Referrals'
                    elif list_name == 'TA Waiting List':
                        axis_title = 'Patients'
                    
                    st.subheader('') 

                    fig = px.line(
                                asst_referrals_col2_filtered,
                                x="Week Number",
                                color="Run Number",
                                #line_dash="Run",
                                y="value",
                                labels={
                                        "value": axis_title
                                        },
                                    #facet_row="variable", # show each facet as a row
                                    #facet_col="variable", # show each facet as a column
                                    height=500,
                                    width=350,
                                    title=f'{list_name} by Week'
                                    )
                        
                    fig.update_traces(line=dict(dash='dot'))
                    
                    # get the average waiting list across all the runs
                    weekly_avg_col2 = asst_referrals_col2_filtered.groupby(['Week Number',
                                                    'variable'])['value'].mean(
                                                    ).reset_index()
                    
                    fig.add_trace(
                                go.Scatter(x=weekly_avg_col2["Week Number"],
                                        y=weekly_avg_col2["value"], name='Average',
                                        line=dict(width=3,color='blue')))
        
                    
                    # get rid of 'variable' prefix resulting from df.melt
                    fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                            ("=")[1]))
                    #fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[1]))

                    # fig.update_layout(
                    #     title=dict(text=f'ADHD {'variable'} Waiting Lists by Week, 
                    #               font=dict(size=20), automargin=True, yref='paper')
                    #     ))
                    fig.update_layout(title_x=0.3,font=dict(size=10))
                    #fig.

                    st.plotly_chart(fig, use_container_width=True)

                    st.divider()

        with col3:

            for i, list_name in enumerate(asst_referrals_col3_unpivot['variable']
                                            .unique()):

                asst_referrals_col3_filtered = asst_referrals_col3_unpivot[
                                    asst_referrals_col3_unpivot["variable"]==list_name]
                
                if list_name == 'Accepted Referrals':
                        axis_title = 'Referrals'
                elif list_name == 'TA Accept':
                    axis_title = 'Patients'

                st.subheader('') 
                
                fig = px.line(
                            asst_referrals_col3_filtered,
                            x="Week Number",
                            color="Run Number",
                            #line_dash="Run",
                            y="value",
                            labels={
                                    "value": axis_title
                                    },
                                #facet_row="variable", # show each facet as a row
                                #facet_col="variable", # show each facet as a column
                                height=500,
                                width=350,
                                title=f'{list_name} by Week'
                                )
                    
                fig.update_traces(line=dict(dash='dot'))
                
                # get the average waiting list across all the runs
                weekly_avg_col3 = asst_referrals_col3_filtered.groupby(['Week Number',
                                                'variable'])['value'].mean(
                                                ).reset_index()
                
                fig.add_trace(
                            go.Scatter(x=weekly_avg_col3["Week Number"],
                                    y=weekly_avg_col3["value"], name='Average',
                                    line=dict(width=3,color='blue')))
    
                
                # get rid of 'variable' prefix resulting from df.melt
                fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                        ("=")[1]))
                #fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[1]))

                # fig.update_layout(
                #     title=dict(text=f'ADHD {'variable'} Waiting Lists by Week, 
                #               font=dict(size=20), automargin=True, yref='paper')
                #     ))
                fig.update_layout(title_x=0.3,font=dict(size=10))
                #fig.

                st.plotly_chart(fig, use_container_width=True)

                st.divider()

        # ########## Step2 Tab ##########

        ########## CBT ##########
        with tab2:

            st.header('Step 2')

            col1, col2 = st.columns(2)

            with col1:

                st.subheader('Psychological Wellbeing Practitioner - 1:1')
            
                for i, list_name in enumerate(pwp_combined_summary['variable']
                                            .unique()):
                  
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                    if list_name == 'Session Number':
                        axis_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        axis_title = 'Patients'

                    pwp_combined_col1_filtered = pwp_combined_summary[
                                        pwp_combined_summary["variable"]==list_name]
                    
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    
                        fig = px.histogram(pwp_combined_col1_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['green'],
                                            title=f'Number of Sessions per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                        fig = px.line(
                                    pwp_combined_col1_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Patients'
                                        },
                                    height=500,
                                    width=350,
                                    title='Number of Patients Waiting by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting list across all the runs
                        weekly_avg_col1 = pwp_combined_col1_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col1["Week Number"],
                                            y=weekly_avg_col1["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                       
                        fig.update_layout(title_x=0.3,font=dict(size=10))
                        #fig.

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

            with col2:            
                              
                if list_name == 'IsDNA':
                    axis_title = 'DNAs'
                elif list_name == 'Q Time':
                    axis_title = 'Weeks'

                st.subheader('')

                for i, list_name in enumerate(pwp_combined_summary['variable']
                                            .unique()):

                    pwp_combined_col2_filtered = pwp_combined_summary[
                                        pwp_combined_summary["variable"]==list_name]
                    
                    if list_name == 'IsDNA':
                        
                        section_title = ''
                    
                        fig = px.histogram(pwp_combined_col2_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['red'],
                                            title=f'Number of DNAs per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'Q Time':

                        section_title = ''

                        fig = px.line(
                                    pwp_combined_col2_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Weeks'
                                        },
                                    height=500,
                                    width=350,
                                    title='Average Waiting Time by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting time across all the runs
                        weekly_avg_col2 = pwp_combined_col2_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col2["Week Number"],
                                            y=weekly_avg_col2["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                        
                        fig.update_layout(title_x=0.3,font=dict(size=10))

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

            ########## Groups ##########

            col1, col2 = st.columns(2)

            with col1:

                st.subheader('Psychological Wellbeing Practitioner - Groups')
            
                for i, list_name in enumerate(group_combined_summary['variable']
                                            .unique()):
                  
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                    if list_name == 'Session Number':
                        axis_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        axis_title = 'Patients'

                    group_combined_col1_filtered = group_combined_summary[
                                        group_combined_summary["variable"]==list_name]
                    
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    
                        fig = px.histogram(group_combined_col1_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['green'],
                                            title=f'Number of Sessions per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                        fig = px.line(
                                    group_combined_col1_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Patients'
                                        },
                                    height=500,
                                    width=350,
                                    title='Number of Patients Waiting by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting list across all the runs
                        weekly_avg_col1 = group_combined_col1_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col1["Week Number"],
                                            y=weekly_avg_col1["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                       
                        fig.update_layout(title_x=0.3,font=dict(size=10))
                        #fig.

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

            with col2:            
                              
                if list_name == 'IsDNA':
                    axis_title = 'DNAs'
                elif list_name == 'Q Time':
                    axis_title = 'Weeks'

                st.subheader('')

                for i, list_name in enumerate(group_combined_summary['variable']
                                            .unique()):

                    group_combined_col2_filtered = group_combined_summary[
                                        group_combined_summary["variable"]==list_name]
                    
                    if list_name == 'IsDNA':
                        
                        section_title = ''
                    
                        fig = px.histogram(group_combined_col2_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['red'],
                                            title=f'Number of DNAs per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'Q Time':

                        section_title = ''

                        fig = px.line(
                                    group_combined_col2_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Weeks'
                                        },
                                    height=500,
                                    width=350,
                                    title='Average Waiting Time by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting time across all the runs
                        weekly_avg_col2 = group_combined_col2_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col2["Week Number"],
                                            y=weekly_avg_col2["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                        
                        fig.update_layout(title_x=0.3,font=dict(size=10))

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()
        
        # ########## Step3 Tab ##########

        ########## CBT ##########
        with tab3:

            st.header('Step 3')

            col1, col2 = st.columns(2)

            with col1:

                st.subheader('Cognitive Behavioural Therapy')
            
                for i, list_name in enumerate(cbt_combined_summary['variable']
                                            .unique()):
                  
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                    if list_name == 'Session Number':
                        axis_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        axis_title = 'Patients'

                    cbt_combined_col1_filtered = cbt_combined_summary[
                                        cbt_combined_summary["variable"]==list_name]
                    
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    
                        fig = px.histogram(cbt_combined_col1_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['green'],
                                            title=f'Number of Sessions per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                        fig = px.line(
                                    cbt_combined_col1_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Patients'
                                        },
                                    height=500,
                                    width=350,
                                    title='Number of Patients Waiting by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting list across all the runs
                        weekly_avg_col1 = cbt_combined_col1_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col1["Week Number"],
                                            y=weekly_avg_col1["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                       
                        fig.update_layout(title_x=0.3,font=dict(size=10))
                        #fig.

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

            with col2:            
                              
                if list_name == 'IsDNA':
                    axis_title = 'DNAs'
                elif list_name == 'Q Time':
                    axis_title = 'Weeks'

                st.subheader('')

                for i, list_name in enumerate(cbt_combined_summary['variable']
                                            .unique()):

                    cbt_combined_col2_filtered = cbt_combined_summary[
                                        cbt_combined_summary["variable"]==list_name]
                    
                    if list_name == 'IsDNA':
                        
                        section_title = ''
                    
                        fig = px.histogram(cbt_combined_col2_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['red'],
                                            title=f'Number of DNAs per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'Q Time':

                        section_title = ''

                        fig = px.line(
                                    cbt_combined_col2_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Weeks'
                                        },
                                    height=500,
                                    width=350,
                                    title='Average Waiting Time by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting time across all the runs
                        weekly_avg_col2 = cbt_combined_col2_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col2["Week Number"],
                                            y=weekly_avg_col2["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                        
                        fig.update_layout(title_x=0.3,font=dict(size=10))

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

            ########## Counselling ##########

            col1, col2 = st.columns(2)

            with col1:

                st.subheader('Depression Counselling')
            
                for i, list_name in enumerate(couns_combined_summary['variable']
                                            .unique()):
                  
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                    if list_name == 'Session Number':
                        axis_title = 'Sessions'
                    elif list_name == 'WL Posn':
                        axis_title = 'Patients'

                    couns_combined_col1_filtered = couns_combined_summary[
                                        couns_combined_summary["variable"]==list_name]
                    
                    if list_name == 'Session Number':
                        section_title = 'Sessions'
                    
                        fig = px.histogram(couns_combined_col1_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['green'],
                                            title=f'Number of Sessions per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'WL Posn':
                        section_title = 'Waiting List'

                        fig = px.line(
                                    couns_combined_col1_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Patients'
                                        },
                                    height=500,
                                    width=350,
                                    title='Number of Patients Waiting by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting list across all the runs
                        weekly_avg_col1 = couns_combined_col1_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col1["Week Number"],
                                            y=weekly_avg_col1["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                       
                        fig.update_layout(title_x=0.3,font=dict(size=10))
                        #fig.

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

            with col2:            
                              
                if list_name == 'IsDNA':
                    axis_title = 'DNAs'
                elif list_name == 'Q Time':
                    axis_title = 'Weeks'

                st.subheader('')

                for i, list_name in enumerate(couns_combined_summary['variable']
                                            .unique()):

                    couns_combined_col2_filtered = couns_combined_summary[
                                        couns_combined_summary["variable"]==list_name]
                    
                    if list_name == 'IsDNA':
                        
                        section_title = ''
                    
                        fig = px.histogram(couns_combined_col2_filtered, 
                                            x='Week Number',
                                            y='value',
                                            nbins=sim_duration_input,
                                            labels={'value': 'Sessions'},
                                            color_discrete_sequence=['red'],
                                            title=f'Number of DNAs per Week')
                        
                        fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
                        
                        fig.update_traces(marker_line_color='black', marker_line_width=1)

                        fig.update_yaxes(title_text="Sessions")

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

                    elif list_name == 'Q Time':

                        section_title = ''

                        fig = px.line(
                                    couns_combined_col2_filtered,
                                    x="Week Number",
                                    color="Run Number",
                                    #line_dash="Run",
                                    y="value",
                                    labels={
                                            "value": 'Weeks'
                                        },
                                    height=500,
                                    width=350,
                                    title='Average Waiting Time by Week'
                                    )
                        
                        fig.update_traces(line=dict(dash='dot'))
                        
                        # get the average waiting time across all the runs
                        weekly_avg_col2 = couns_combined_col2_filtered.groupby(['Week Number',
                                                        'variable'])['value'].mean(
                                                        ).reset_index()
                        
                        fig.add_trace(
                                    go.Scatter(x=weekly_avg_col2["Week Number"],
                                            y=weekly_avg_col2["value"], name='Average',
                                            line=dict(width=3,color='blue')))
            
                        
                        # get rid of 'variable' prefix resulting from df.melt
                        fig.for_each_annotation(lambda a: a.update(text=a.text.split
                                                                ("=")[1]))
                        
                        fig.update_layout(title_x=0.3,font=dict(size=10))

                        st.plotly_chart(fig, use_container_width=True)

                        st.divider()

        ########## Job Plans ##########
        with tab4:

            # st.write(cbt_sessions_weekly_summary)
            # st.write(cbt_sessions_summary)
            # st.write(cbt_hours_weekly_summary)
            #st.write(couns_sessions_weekly_summary)
            st.header('Job Plans')

            ##### PwP Practitioner #####

            st.subheader('Psychological Wellbeing Practitioners')

            fig = px.histogram(pwp_hours_weekly_summary, 
                                x='Week Number',
                                y='value',
                                nbins=sim_duration_input,
                                labels={'value': 'Hours'
                                        ,'variable':'Time Alloc'},
                                color='variable',
                                color_discrete_sequence=px.colors.qualitative.Dark24,
                                title=f'Psychological Wellbeing Practitioner Hours by Week')
            
            fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig.update_traces(marker_line_color='black', marker_line_width=1)

            # add line for available PwP hours
            fig.add_trace(
                                go.Scatter(x=pwp_hours_weekly_summary["Week Number"],
                                        y=np.repeat(total_pwp_hours,sim_duration_input*2),
                                        name='Avail Hrs',line=dict(width=3,
                                        color='green')))

            st.plotly_chart(fig, use_container_width=True)

            st.divider() 

            ##### CBT Practitioner #####

            st.subheader('Cognitive Behavioural Therapists')

            fig = px.histogram(cbt_hours_weekly_summary, 
                                x='Week Number',
                                y='value',
                                nbins=sim_duration_input,
                                labels={'value': 'Hours'
                                        ,'variable':'Time Alloc'},
                                color='variable',
                                color_discrete_sequence=px.colors.qualitative.Dark24,
                                title=f'Cognitive Behavioural Therapist Hours by Week')
            
            fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig.update_traces(marker_line_color='black', marker_line_width=1)

            # add line for available PwP hours
            fig.add_trace(
                                go.Scatter(x=cbt_hours_weekly_summary["Week Number"],
                                        y=np.repeat(total_cbt_hours,sim_duration_input*2),
                                        name='Avail Hrs',line=dict(width=3,
                                        color='green')))

            st.plotly_chart(fig, use_container_width=True)

            st.divider()   

            ##### Couns Practitioner #####

            st.subheader('Depression Counselling Therapists')

            fig = px.histogram(couns_hours_weekly_summary, 
                                x='Week Number',
                                y='value',
                                nbins=sim_duration_input,
                                labels={'value': 'Hours'
                                        ,'variable':'Time Alloc'},
                                color='variable',
                                color_discrete_sequence=px.colors.qualitative.Dark24,
                                title=f'Depression Counselling Therapist Hours by Week')
            
            fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
            fig.update_traces(marker_line_color='black', marker_line_width=1)

            # add line for available PwP hours
            fig.add_trace(
                                go.Scatter(x=couns_hours_weekly_summary["Week Number"],
                                        y=np.repeat(total_couns_hours,sim_duration_input*2),
                                        name='Avail Hrs',line=dict(width=3,
                                        color='green')))

            st.plotly_chart(fig, use_container_width=True)

            st.divider()   

    