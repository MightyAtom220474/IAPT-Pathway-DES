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

st.logo("https://lancsvp.org.uk/wp-content/uploads/2021/08/nhs-logo-300x189.png")

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
                                          min_value=100,max_value=200,
                                          step=1,value = g.number_staff_cbt)
        couns_avail_input = st.number_input(label="Starting Number of Counselling Practitioners WTE",
                                            min_value=1,max_value=100,
                                            step=1,value = g.number_staff_couns)
        pwp_avail_input = st.number_input(label="Starting Number of PwP Practitioners WTE",
                                          min_value=100,max_value=200,
                                          step=1,value = g.number_staff_pwp)
        cbt_add_input = st.number_input("Additional Number of CBT Practitioners WTE",
                        min_value=0, max_value=20, step=1, value=0)
        couns_add_input = st.number_input("Additional Number of Counselling Practitioners WTE",
                        min_value=0, max_value=20, step=1, value=0)
        pwp_add_input = st.number_input("Additional Number of PwP Practitioners WTE",
                        min_value=0, max_value=20, step=1, value=0)
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
        number_of_runs_input = st.slider("Number of Simulation Runs", 1, 20, 3)

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
# calculate total hours for job plans
total_cbt_hours = cbt_avail_input*cbt_hours_avail_input
total_couns_hours = couns_avail_input*couns_hours_avail_input
total_pwp_hours = pwp_avail_input*pwp_hours_avail_input

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
        step2_results_df, step2_sessions_df, step3_results_df, step3_sessions_df, asst_weekly_dfs, staff_weekly_dfs, caseload_weekly_dfs = my_trial.run_trial()
        

        st.subheader(f'Summary of all {g.number_of_runs} Simulation Runs over {g.sim_duration}'
                     f' Weeks with {cbt_add_input} additional CBT,'
                      f' {couns_add_input} additional Counsellors and '
                      f'{pwp_add_input} additional PwP Practitioners')
        
        # turn asst values from running total to weekly total
        #asst_weekly_dfs['Referrals Recvd'] = (asst_weekly_dfs['Referrals Received']-asst_weekly_dfs['Referrals Received'].shift(1))
        asst_weekly_dfs['Referral Screen Hrs'] = (asst_weekly_dfs['Referral Screen Mins']-asst_weekly_dfs['Referral Screen Mins'].shift(1))/60
        asst_weekly_dfs['Rejected Referrals'] = (asst_weekly_dfs['Referrals Rejected']-asst_weekly_dfs['Referrals Rejected'].shift(1))
        asst_weekly_dfs['Referral Reviews'] = asst_weekly_dfs['Referrals Reviewed']#-asst_weekly_dfs['Referrals Reviewed'].shift(1))
        asst_weekly_dfs['Reviewed Rejected'] = asst_weekly_dfs['Reviews Rejected']#-asst_weekly_dfs['Reviews Rejected'].shift(1))
        asst_weekly_dfs['Optin Total'] = (asst_weekly_dfs['Referrals Opted-in']-asst_weekly_dfs['Referrals Opted-in'].shift(1))
        #asst_weekly_dfs['TA Waiting List'] = (asst_weekly_dfs['TA Waiting List']-asst_weekly_dfs['TA Waiting List'].shift(1))
        asst_weekly_dfs['TA Accept'] = (asst_weekly_dfs['TA Total Accept']-asst_weekly_dfs['TA Total Accept'].shift(1))

        # get rid of negative values
        num = asst_weekly_dfs._get_numeric_data()

        num[num < 0] = 0

        asst_weekly_dfs['Accepted Referrals'] = asst_weekly_dfs['Referrals Received']-asst_weekly_dfs['Rejected Referrals']
        
        # filter dataframe to just return columns needed
        asst_weekly_summary = asst_weekly_dfs[['Run Number','Week Number','Referrals Received','Referral Screen Hrs','Accepted Referrals','Rejected Referrals','Referral Reviews','Reviewed Rejected','Optin Total','TA Waiting List','TA Avg Wait','TA Accept']]
               
        asst_weekly_summary = asst_weekly_summary[asst_weekly_summary["Week Number"] != 0]
        
        step2_pwp_results_summary = step2_results_df[
                                    step2_results_df["Route Name"]=='PwP']
        
        step2_pwp_sessions_summary = step2_sessions_df[
                                    step2_sessions_df["Route Name"]=='PwP']
        
        step2_group_results_summary = step2_results_df[
                                    step2_results_df["Route Name"]=='Group']
        
        step2_group_sessions_summary = step2_sessions_df[
                                    step2_sessions_df["Route Name"]=='Group']
        
        step3_cbt_results_summary = step3_results_df[
                                    step3_results_df["Route Name"]=='CBT']
        
        step3_cbt_sessions_summary = step3_sessions_df[
                                    step3_sessions_df["Route Name"]=='CBT']
        
        step3_couns_results_summary = step3_results_df[
                                    step3_results_df["Route Name"]=='Couns']
        
        step3_couns_sessions_summary = step3_sessions_df[
                                    step3_sessions_df["Route Name"]=='Couns']
        
        dataframes = {}

        # Store melted & aggregated DataFrames in a dictionary
        aggregated_dfs = {'step2_pwp_results_summary':step2_pwp_results_summary,'step2_pwp_sessions_summary':step2_pwp_sessions_summary
                          ,'step2_group_results_summary':step2_group_results_summary,'step2_group_sessions_summary':step2_group_sessions_summary
                          ,'step3_cbt_results_summary':step3_cbt_results_summary,'step3_cbt_sessions_summary':step3_cbt_sessions_summary
                          ,'step3_couns_results_summary':step3_couns_results_summary,'step3_couns_sessions_summary':step3_couns_sessions_summary}

        for name, df in dataframes.items():
            # Melt the DataFrame
            melted_df = pd.melt(df, id_vars=['Run Number','Week Number'], var_name='Variable', value_name='Value')

            # Apply different aggregations based on column names
            aggregated_df = melted_df.groupby(['Run Number','Week Number','Variable']).agg(
                {'Value': lambda x: x.sum() if x.name in ['Session Time', 'Admin Time','IsDNA'] else x.count()}
            ).reset_index()

            # Store the result
            aggregated_dfs[name] = aggregated_df

            # # Access melted + aggregated DataFrames separately
            # print(aggregated_dfs['df1'])  # Aggregated df1
            # print(aggregated_dfs['df2'])  # Aggregated df2
    
        with st.expander("See explanation"):
            st.write('This Simulation is designed to replicate the flow '
                     'of patients through the Talking Therapies Assessment and'
                     'Treatment Pathway.')

        ##### get all data structured correctly #####

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
        
        # df_weekly_rej = df_weekly_stats[['Run','Week Number','Triage Rejects',
        #                                  'MDT Rejects','Asst Rejects']]

        # df_weekly_rej_unpivot = pd.melt(df_weekly_rej, 
        #                                 value_vars=['Triage Rejects',
        #                                             'MDT Rejects',
        #                                             'Asst Rejects'],
        #                                             id_vars=['Run',
        #                                             'Week Number'])

        # df_weekly_wt = df_weekly_stats[['Run','Week Number','Triage Wait',
        #                                 'MDT Wait','Asst Wait']]

        # df_weekly_wt_unpivot = pd.melt(df_weekly_wt, value_vars=['Triage Wait',
        #                                 'MDT Wait','Asst Wait'], id_vars=['Run',
        #                                 'Week Number'])
        
        # ########## Clinical & Admin Tab ##########
        
        # ##### get all data structured correctly #####

        # ##### Top - 1 chart #####

        # df_weekly_ref_screen = df_weekly_stats[['Run','Week Number',
        #                                         'Referral Screen Hrs']]
                  
        # ##### Upper Middle - 3 columns 1 row #####

        # df_weekly_triage_clin = df_weekly_stats[['Run','Week Number',
        #                                         'Triage Clin Hrs']]
        
        # df_weekly_triage_admin = df_weekly_stats[['Run','Week Number',
        #                                         'Triage Admin Hrs']]
        
        # df_weekly_triage_rej = df_weekly_stats[['Run','Week Number',
        #                                         'Triage Reject Hrs']]
        # ##### Middle - 2 columns 2 rows #####

        # df_weekly_col4 = df_weekly_stats[['Run','Week Number','Pack Send Hrs',
        #                                 'Obs Visit Hrs']]
        
        # df_weekly_col4_unpivot = pd.melt(df_weekly_col4, value_vars=[
        #                                 'Pack Send Hrs',
        #                                 'Obs Visit Hrs'],
        #                                 id_vars=['Run','Week Number'])
        
        # df_weekly_col5 = df_weekly_stats[['Run','Week Number','Pack Reject Hrs',
        #                                 'Obs Reject Hrs']]
        
        # df_weekly_col5_unpivot = pd.melt(df_weekly_col5, value_vars=[
        #                                 'Pack Reject Hrs',
        #                                 'Obs Reject Hrs'],
        #                                 id_vars=['Run','Week Number'])
        
        # ##### Lower Middle - 3 columns 1 row #####

        # df_weekly_mdt_prep = df_weekly_stats[['Run','Week Number',
        #                                         'MDT Prep Hrs']]
        
        # df_weekly_mdt_meet = df_weekly_stats[['Run','Week Number',
        #                                         'MDT Meet Hrs']]
        
        # df_weekly_mdt_rej = df_weekly_stats[['Run','Week Number',
        #                                         'MDT Reject Hrs']]

        # ##### Bottom - 2 columns 2 rows #####
        
        # df_weekly_col9 = df_weekly_stats[['Run','Week Number',
        #                                 'Asst Clin Hrs','Diag Reject Hrs']]
        
        # df_weekly_col9_unpivot = pd.melt(df_weekly_col9, value_vars=[
        #                                 'Asst Clin Hrs','Diag Reject Hrs'],
        #                                 id_vars=['Run','Week Number'])
        
        # df_weekly_col10 = df_weekly_stats[['Run','Week Number',
        #                                 'Asst Admin Hrs','Diag Accept Hrs']]
        
        # df_weekly_col10_unpivot = pd.melt(df_weekly_col10, value_vars=[
        #                                 'Asst Admin Hrs','Diag Accept Hrs'],
        #                                 id_vars=['Run','Week Number'])
        
        # ########## Job Plans Tab ##########

        # ##### Band 6 Practitioner

        # df_weekly_b6 = df_weekly_stats[['Run','Week Number',
        #                                 'Referral Screen Hrs','Triage Clin Hrs',
        #                                 'Triage Admin Hrs','Triage Reject Hrs',
        #                                 'Pack Reject Hrs','Obs Reject Hrs',
        #                                 'MDT Reject Hrs',
        #                                 'Asst Clin Hrs','Asst Admin Hrs',
        #                                 'Diag Accept Hrs','Diag Reject Hrs']]

        # df_weekly_b6_avg = df_weekly_b6.groupby(['Week Number'], as_index=False).mean()
        
        # df_weekly_b6_unpivot = pd.melt(df_weekly_b6_avg, value_vars=[
        #                                 'Referral Screen Hrs','Triage Clin Hrs',
        #                                 'Triage Admin Hrs','Triage Reject Hrs',
        #                                 'Pack Reject Hrs','Obs Reject Hrs',
        #                                 'MDT Reject Hrs',
        #                                 'Asst Clin Hrs','Asst Admin Hrs',
        #                                 'Diag Accept Hrs','Diag Reject Hrs'],
        #                                 id_vars=['Week Number'])
        
        # ##### Band 4 Practitioner

        # df_weekly_b4 = df_weekly_stats[['Run','Week Number',
        #                                 'Obs Visit Hrs','Obs Reject Hrs',
        #                                 'MDT Prep Hrs','MDT Meet Hrs']]

        # df_weekly_b4_avg = df_weekly_b4.groupby(['Week Number'], as_index=False).mean()

        # df_weekly_b4_unpivot = pd.melt(df_weekly_b4_avg, value_vars=[
        #                                 'Obs Visit Hrs','Obs Reject Hrs',
        #                                 'MDT Prep Hrs','MDT Meet Hrs'],
        #                                 id_vars=['Week Number'])
        
                       
        tab1, tab2, tab3, tab4 = st.tabs(["Referral & Assessment", "Step 2","Step 3","Job Plans"])
        
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
                        axis_title = 'Patients'

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
                        axis_title = 'Weeks'
                    
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


        #     # fig2 = px.line(
        #     #                 df_weekly_wl_unpivot,
        #     #                 x="Week Number",
        #     #                 color="Run",
        #     #                 y="value",
        #     #                 labels={
        #     #                         "value": "Waiters",
        #     #                         #"sepal_width": "Sepal Width (cm)",
        #     #                         #"species": "Species of Iris"
        #     #                         },
        #     #                 #facet_row="variable", # show each facet as a row
        #     #                 #facet_col="variable", # show each facet as a column
        #     #                 height=800,
                            
        #     #                 )
        #     # # get rid of 'variable' prefix resulting from df.melt
        #     # fig2.for_each_annotation(lambda a: a.update(text=a.text.split("=")[1]))
        #     # #fig.for_each_trace(lambda t: t.update(name=t.name.split("=")[1]))

        #     # # fig.update_layout(
        #     # #     title=dict(text=f'ADHD {'variable'} Waiting Lists by Week, 
        #     #                   font=dict(size=20), automargin=True, yref='paper')
        #     # #     ))
        #     # fig2.update_layout(title_x=0.4)
        #     # #fig.

        #     # st.plotly_chart(fig2, use_container_width=True)
        #     # # with col1:
        #     # #     st.write(df_trial_results)

        #     #     @st.fragment
        #     #     def download_1():
        #     #         st.download_button(
        #     #             "Click here to download the data in a csv format",
        #     #             df_trial_results.to_csv().encode('utf-8'),
        #     #             f"trial_summary_{g.number_of_clinicians}_clinicians_{
        #     #             g.mean_referrals}_referrals.csv","text/csv")
        #     #     download_1()

        #     # fig = px.line(weekly_wl_position,x="Week Number" ,y="Waiting List",
        #     #               color="Run Number",
        #     #               title='ADHD Diagnosis Waiting List by Week')

        #     # fig.update_traces(line=dict(color="Blue", width=0.5))

        #     # fig.update_layout(title_x=0.4)

        #     # fig.add_trace(
        #     #     go.Scatter(x=weekly_avg_wl["Week Number"],y=weekly_avg_wl[
        #     #                               "Waiting List"], name='Average'))

        #     # fig.update_layout(xaxis_title='Week Number',
        #     #                 yaxis_title='Patients Waiting')

        #     # with col2:
        #     #     st.plotly_chart(fig, use_container_width=True)

        #     #     @st.fragment
        #     #     def download_2():
        #     #         # Create an in-memory buffer
        #     #         buffer = io.BytesIO()
        #     #         fig.write_image(file=buffer,format='pdf')
        #     #         st.download_button(label='Click here to Download Chart as PDF'
        #     #         ,data=buffer, file_name='waiting_list',
        #     #         mime='application/octet-stream')
        #     #     download_2()


        # ########## Clinical & Admin Tab ##########

        # with tab2:

        #     st.subheader('Referrals')

        #     ##### Referral Screening #####

        #     df_ref_screen_avg = df_weekly_ref_screen.groupby(['Week Number'])['Referral Screen Hrs'].mean().reset_index()
            
        #     fig = px.histogram(df_ref_screen_avg, 
        #                         x='Week Number',
        #                         y='Referral Screen Hrs',
        #                         nbins=sim_duration_input,
        #                         labels={'Referral Screen Hrs': 'Hours'},
        #                         color_discrete_sequence=['green'],
        #                         title=f'Referral Screening Hours by Week')
            
        #     fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
            
        #     fig.update_traces(marker_line_color='black', marker_line_width=1)
        #     #fig.

        #     st.plotly_chart(fig, use_container_width=True)

        #     st.divider()

        #     ##### Triage #####

        #     col1, col2, col3 = st.columns(3)

        #     with col1:

        #         st.subheader('Triage')

        #         df_triage_clin_avg = df_weekly_triage_clin.groupby(['Week Number'])['Triage Clin Hrs'].mean().reset_index()
                
        #         fig = px.histogram(df_triage_clin_avg, 
        #                             x='Week Number',
        #                             y='Triage Clin Hrs',
        #                             nbins=sim_duration_input,
        #                             labels={'Triage Clin Hrs': 'Hours'},
        #                             color_discrete_sequence=['green'],
        #                             title=f'Triage Clinical Hours by Week')
                
        #         fig.update_layout(title_x=0.3,font=dict(size=10),bargap=0.2)
                
        #         fig.update_traces(marker_line_color='black', marker_line_width=1)
        #         #fig.

        #         st.plotly_chart(fig, use_container_width=True)

        #         st.divider()

        #     with col2:

        #         st.subheader('')

        #         df_triage_admin_avg = df_weekly_triage_admin.groupby(['Week Number'])['Triage Admin Hrs'].mean().reset_index()
                
        #         fig = px.histogram(df_triage_admin_avg, 
        #                             x='Week Number',
        #                             y='Triage Admin Hrs',
        #                             nbins=sim_duration_input,
        #                             labels={'Triage Admin Hrs': 'Hours'},
        #                             color_discrete_sequence=['blue'],
        #                             title=f'Triage Admin Hours by Week')
                
        #         fig.update_layout(title_x=0.3,font=dict(size=10),bargap=0.2)
                
        #         fig.update_traces(marker_line_color='black', marker_line_width=1)
        #         #fig.

        #         st.plotly_chart(fig, use_container_width=True)

        #         st.divider()

        #     with col3:

        #         st.subheader('')

        #         df_triage_rej_avg = df_weekly_triage_rej.groupby(['Week Number'])['Triage Reject Hrs'].mean().reset_index()
                
        #         fig = px.histogram(df_triage_rej_avg, 
        #                             x='Week Number',
        #                             y='Triage Reject Hrs',
        #                             nbins=sim_duration_input,
        #                             labels={'Triage Reject Hrs': 'Hours'},
        #                             color_discrete_sequence=['red'],
        #                             title=f'Triage Rejection Hours by Week')
                
        #         fig.update_layout(title_x=0.3,font=dict(size=10),bargap=0.2)
                
        #         fig.update_traces(marker_line_color='black', marker_line_width=1)
        #         #fig.

        #         st.plotly_chart(fig, use_container_width=True)

        #         st.divider()

        #     ##### Pack & Obs #####

        #     col4, col5 = st.columns(2)
            
        #     with col4:
            
        #         for i, list_name in enumerate(df_weekly_col4_unpivot['variable']
        #                                     .unique()):

        #             if list_name == 'Pack Send Hrs':
        #                 section_title = 'Information Packs'
        #             elif list_name == 'Obs Visit Hrs':
        #                 section_title = 'Observations'

        #             if list_name == 'Pack Send Hrs':
        #                 chart_colour = 'blue'
        #             elif list_name == 'Obs Visit Hrs':
        #                 chart_colour = 'green'
                    
        #             st.subheader(section_title)

        #             df_weekly_col4_filtered = df_weekly_col4_unpivot[
        #                                 df_weekly_col4_unpivot["variable"]==list_name]
                    
        #             weekly_avg_hrs_col4 = df_weekly_col4_filtered.groupby(['variable',
        #                                             'Week Number'])['value'
        #                                             ].mean().reset_index()
                    
        #             fig = px.histogram(weekly_avg_hrs_col4, 
        #                                x="Week Number",
        #                                y='value',
        #                                nbins=sim_duration_input,
        #                                labels={"value": "Hours"},
        #                                color_discrete_sequence=[chart_colour],
        #                                title=f'{list_name} by Week')
                   
        #             # get rid of 'variable' prefix resulting from df.melt
        #             fig.for_each_annotation(lambda a: a.update(text=a.text.split
        #                                                     ("=")[1]))
        #             fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
        #             fig.update_traces(marker_line_color='black', marker_line_width=1)
        #             #fig.

        #             st.plotly_chart(fig, use_container_width=True)

        #             st.divider()

        #     with col5:
            
        #         for i, list_name in enumerate(df_weekly_col5_unpivot['variable']
        #                                     .unique()):

        #             st.subheader('')
                    
        #             df_weekly_col5_filtered = df_weekly_col5_unpivot[
        #                                 df_weekly_col5_unpivot["variable"]==list_name]
                    
        #             weekly_avg_hrs_col5 = df_weekly_col5_filtered.groupby(['variable',
        #                                             'Week Number'])['value'
        #                                             ].mean().reset_index()
                    
        #             fig = px.histogram(weekly_avg_hrs_col5, 
        #                                x="Week Number",
        #                                y='value',
        #                                nbins=sim_duration_input,
        #                                labels={"value": "Hours"},
        #                                color_discrete_sequence=["red"],
        #                                title=f'{list_name} by Week')
                   
        #             # get rid of 'variable' prefix resulting from df.melt
        #             fig.for_each_annotation(lambda a: a.update(text=a.text.split
        #                                                     ("=")[1]))
        #             fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
        #             fig.update_traces(marker_line_color='black', marker_line_width=1)
        #             #fig.

        #             st.plotly_chart(fig, use_container_width=True)

        #             st.divider()

        #     ##### MDT #####
            
        #     col6, col7, col8 = st.columns(3)

        #     with col6:

        #         st.subheader('MDT')

        #         df_mdt_prep_avg = df_weekly_mdt_prep.groupby(['Week Number'])['MDT Prep Hrs'].mean().reset_index()
                
        #         fig = px.histogram(df_mdt_prep_avg, 
        #                             x='Week Number',
        #                             y='MDT Prep Hrs',
        #                             nbins=sim_duration_input,
        #                             labels={'MDT Prep Hrs': 'Hours'},
        #                             color_discrete_sequence=['blue'],
        #                             title=f'MDT Prep Hours by Week')
                
        #         fig.update_layout(title_x=0.3,font=dict(size=10),bargap=0.2)
                
        #         fig.update_traces(marker_line_color='black', marker_line_width=1)
        #         #fig.

        #         st.plotly_chart(fig, use_container_width=True)

        #         st.divider()

        #     with col7:

        #         st.subheader('')

        #         df_mdt_meet_avg = df_weekly_mdt_meet.groupby(['Week Number'])['MDT Meet Hrs'].mean().reset_index()
                
        #         fig = px.histogram(df_mdt_meet_avg, 
        #                             x='Week Number',
        #                             y='MDT Meet Hrs',
        #                             nbins=sim_duration_input,
        #                             labels={'MDT Meet Hrs': 'Hours'},
        #                             color_discrete_sequence=['goldenrod'],
        #                             title=f'MDT Meeting Hours by Week')
                
        #         fig.update_layout(title_x=0.3,font=dict(size=10),bargap=0.2)
                
        #         fig.update_traces(marker_line_color='black', marker_line_width=1)
        #         #fig.

        #         st.plotly_chart(fig, use_container_width=True)

        #         st.divider()

        #     with col8:

        #         st.subheader('')

        #         df_mdt_rej_avg = df_weekly_mdt_rej.groupby(['Week Number'])['MDT Reject Hrs'].mean().reset_index()
                
        #         fig = px.histogram(df_mdt_rej_avg, 
        #                             x='Week Number',
        #                             y='MDT Reject Hrs',
        #                             nbins=sim_duration_input,
        #                             labels={'MDT Reject Hrs': 'Hours'},
        #                             color_discrete_sequence=['red'],
        #                             title=f'MDT Rejection Hours by Week')
                
        #         fig.update_layout(title_x=0.3,font=dict(size=10),bargap=0.2)
                
        #         fig.update_traces(marker_line_color='black', marker_line_width=1)
        #         #fig.

        #         st.plotly_chart(fig, use_container_width=True)

        #         st.divider()

        #     ##### Asst & Diagnosis #####

        #     col9, col10 = st.columns(2)
            
        #     with col9:
            
        #         for i, list_name in enumerate(df_weekly_col9_unpivot['variable']
        #                                     .unique()):

        #             if list_name == 'Asst Clin Hrs':
        #                 section_title = 'Assessment'
        #             elif list_name == 'Diag Reject Hrs':
        #                 section_title = 'Diagnosis'

        #             if list_name == 'Asst Clin Hrs':
        #                 chart_colour = 'green'
        #             elif list_name == 'Diag Reject Hrs':
        #                 chart_colour = 'red'

        #             st.subheader(section_title)

        #             df_weekly_col9_filtered = df_weekly_col9_unpivot[
        #                                 df_weekly_col9_unpivot["variable"]==list_name]
                    
        #             weekly_avg_hrs_col9 = df_weekly_col9_filtered.groupby(['variable',
        #                                             'Week Number'])['value'
        #                                             ].mean().reset_index()
                    
        #             fig = px.histogram(weekly_avg_hrs_col9, 
        #                                x="Week Number",
        #                                y='value',
        #                                nbins=sim_duration_input,
        #                                labels={"value": "Hours"},
        #                                color_discrete_sequence=[chart_colour],
        #                                title=f'{list_name} by Week')
                   
        #             # get rid of 'variable' prefix resulting from df.melt
        #             fig.for_each_annotation(lambda a: a.update(text=a.text.split
        #                                                     ("=")[1]))
        #             fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
        #             fig.update_traces(marker_line_color='black', marker_line_width=1)
        #             #fig.

        #             st.plotly_chart(fig, use_container_width=True)

        #             st.divider()

        #     with col10:
            
        #         for i, list_name in enumerate(df_weekly_col10_unpivot['variable']
        #                                     .unique()):

        #             if list_name == 'Asst Admin Hrs':
        #                 chart_colour = 'blue'
        #             elif list_name == 'Diag Accept Hrs':
        #                 chart_colour = 'green'
                    
        #             st.subheader('')
                    
        #             df_weekly_col10_filtered = df_weekly_col10_unpivot[
        #                                 df_weekly_col10_unpivot["variable"]==list_name]
                    
        #             weekly_avg_hrs_col10 = df_weekly_col10_filtered.groupby(['variable',
        #                                             'Week Number'])['value'
        #                                             ].mean().reset_index()
                    
        #             fig = px.histogram(weekly_avg_hrs_col10, 
        #                                x="Week Number",
        #                                y='value',
        #                                nbins=sim_duration_input,
        #                                labels={"value": "Hours"},
        #                                color_discrete_sequence=[chart_colour],
        #                                title=f'{list_name} by Week')
                   
        #             # get rid of 'variable' prefix resulting from df.melt
        #             fig.for_each_annotation(lambda a: a.update(text=a.text.split
        #                                                     ("=")[1]))
        #             fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2)
        #             fig.update_traces(marker_line_color='black', marker_line_width=1)
        #             #fig.

        #             st.plotly_chart(fig, use_container_width=True)

        #             st.divider()

        # ########## Job Plan Tab ##########

        # with tab3:

        #     st.subheader('Job Plans')

        #     ##### Band 6 Practitioner #####

        #     fig = px.histogram(df_weekly_b6_unpivot, 
        #                         x='Week Number',
        #                         y='value',
        #                         nbins=sim_duration_input,
        #                         labels={'value': 'Hours'
        #                                 ,'variable':'Time Alloc'},
        #                         color='variable',
        #                         color_discrete_sequence=px.colors.qualitative.Dark24,
        #                         title=f'Band 6 Practitioner Hours by Week')
            
        #     fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
        #     fig.update_traces(marker_line_color='black', marker_line_width=1)

        #     # add line for available B4 hours
        #     fig.add_trace(
        #                         go.Scatter(x=weekly_avg_wt["Week Number"],
        #                                 y=np.repeat(total_b6_prac_hours,g.sim_duration),
        #                                 name='Avail Hrs',line=dict(width=3,
        #                                 color='green')))

        #     st.plotly_chart(fig, use_container_width=True)

        #     st.divider()

        #     ##### Band 4 Practitioner #####
            
        #     fig = px.histogram(df_weekly_b4_unpivot, 
        #                         x='Week Number',
        #                         y='value',
        #                         nbins=sim_duration_input,
        #                         labels={'value': 'Hours'
        #                                 ,'variable':'Time Alloc'},
        #                         color='variable',
        #                         color_discrete_sequence=px.colors.qualitative.Light24,
        #                         title=f'Band 4 Practitioner Hours by Week')
            
        #     fig.update_layout(title_x=0.4,font=dict(size=10),bargap=0.2,legend_traceorder="reversed")
            
        #     fig.update_traces(marker_line_color='black', marker_line_width=1)

        #     # add line for available B4 hours
        #     fig.add_trace(
        #                         go.Scatter(x=weekly_avg_wt["Week Number"],
        #                                 y=np.repeat(total_b4_prac_hours,g.sim_duration),
        #                                 name='Avail Hrs',line=dict(width=3,
        #                                 color='green')))
            
        #     st.plotly_chart(fig, use_container_width=True)

        #     st.divider()