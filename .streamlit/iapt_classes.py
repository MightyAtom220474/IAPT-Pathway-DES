import simpy
import random
import numpy as np
import pandas as pd
import math

class g:

    # used for testing
    debug_level = 2

    # Referrals
    mean_referrals_pw = 500

    # Screening
    referral_rej_rate = 0.3 # % of referrals rejected, advised 30%
    referral_review_rate = 0.4 # % that go to MDT as prev contact with Trust
    mdt_freq = 2 # how often in weeks MDT takes place, longest time a review referral may wait for review
    review_rej_rate = 0.5 # % ref that got to MDT and get rejected
    base_waiting_list = 2741 # current number of patients on waiting list
    referral_screen_time = 20 # average time it takes to screen one referral by a pwp
    opt_in_wait = 1 # no. of weeks patients have to opt in
    opt_in_qtime = 4 # longest period a patient will wait for tel assessment based on 4 week window for asst slots
    opt_in_rate = 0.75 # % of referrals that opt-in
    asst_6_weeks = 0.9 # % of referrals that are assessed within 6 weeks

    # TA
    ta_time_mins = 60 # time allocated to each TA
    ta_accept_rate = 0.7 ##### assume 70% of TA's accepted, need to check this #####

    # Step 2
    step2_ratio = 0.85 # proportion of patients that go onto Step2 vs Step3
    step2_routes = ['PwP','Group'] # possible Step2 routes
    step2_path_ratios = [0.8,0.2] #[0.94,0.06] # Step2 proportion for each route
    step2_pwp_sessions = 6 # number of PwP sessions at Step2
    step2_pwp_dna_rate = 0.15 # ##### assume 15% DNA rate for PwP
    step2_pwp_1st_mins = 45 # minutes allocated for 1st pwp session
    step2_pwp_fup_mins = 30 # minutes allocated for pwp follow-up session
    step2_session_admin = 15 # number of mins of clinical admin per session
    step2_pwp_period = 16 # max number of weeks PwP delivered over
    step2_group_sessions = 7 # number of group sessions
    step2_group_size = 7 # size a group needs to be before it can be run
    step2_group_session_mins = 240 # minutes allocated to pwp group session
    step2_group_dna_rate = 0.216 # Wellbeing Workshop attendance 78.6%

    # Step Moves
    step2_step3_ratio = [0.85,0.15]
    step_routes = ['Step2','Step3']
    step_up_rate = 0.01 # proportion of Step2 that get stepped up = 0.3% but rounded up to 1%
    step_down_rate = 0.12 # proportion of Step3 that get stepped down = 11.86%
    
    # Step 3
    step3_ratio = 0.15 # proportion of patients that go onto Step3 vs Step2
    step3_routes =['DepC','CBT'] # full pathway options = ['PfCBT','Group','CBT','EMDR','DepC','DIT','IPT','CDEP']
    step3_path_ratios = [0.368,0.632]# [0.1,0.25,0.25,0.05,0.05,0.1,0.1,0.1] # Step3 proportion for each route ##### Need to clarify exact split
    step3_cbt_sessions = 12 # number of PwP sessions at Step2
    step3_cbt_1st_mins = 45 # minutes allocated for 1st cbt session
    step3_cbt_fup_mins = 30 # minutes allocated for cbt follow-up session
    step3_cbt_dna_rate = 0.216 # Wellbeing Workshop attendance 78.6%
    step3_session_admin = 15 # number of mins of clinical admin per session
    step3_cbt_period = 16 # max number of weeks cbt delivered over
    step3_couns_sessions = 8 # number of couns sessions
    step3_couns_1st_mins = 45 # minutes allocated for 1st couns session
    step3_couns_fup_mins = 30 # minutes allocated for couns follow-up session
    step3_couns_dna_rate = 0.216 # Wellbeing Workshop attendance 78.6%
    step3_couns_period = 16 # max number of weeks couns delivered over

    # Staff
    supervision_time = 120 # 2 hours per month per modality ##### could use modulus for every 4th week
    break_time = 100 # 20 mins per day
    wellbeing_time = 120 # 2 hours allocated per month
    counsellors_huddle = 30 # 30 mins p/w or 1 hr per fortnight
    cpd_time = 225 # half day per month CPD
    
    # Job Plans
    number_staff_cbt = 2
    number_staff_couns = 2
    number_staff_pwp = 3
    hours_avail_cbt = 22.0
    hours_avail_couns = 22.0
    hours_avail_pwp = 21.0
    ta_resource = number_staff_pwp * 3 # job plan = 3 TA per week per PwP
    pwp_resource = number_staff_pwp # starting point for PwP resources
    pwp_res_dict = {}
    pwp_caseload = 30
    pwp_id = 0 # unique ID for PwP resources
    pwp_avail = number_staff_pwp # used to check whether a PwP is available
    group_resource = number_staff_pwp #  job plan = 1 group per week per PwP, assume 12 per group
    cbt_resource = number_staff_cbt # job plan = 2 x 1st + 20 X FUP per cbt per week
    cbt_res_dict = {}
    cbt_caseload = 25
    cbt_id = 0 # unique ID for CBT resources
    cbt_avail = number_staff_cbt # used to check whether a PwP caseload slot is available
    couns_resource = number_staff_couns # job plan = 2 x 1st + 20 X FUP per cbt per week
    couns_res_dict = {}
    couns_caseload = 25
    couns_id = 0 # unique ID for Couns resources
    couns_avail = number_staff_couns # used to check whether a Couns is available

    # Simulation
    sim_duration = 52
    number_of_runs = 1
    std_dev = 3 # used for randomising activity times
    
    # Result storage
    weekly_wl_posn = pd.DataFrame() # container to hold w/l position at end of week
    caseload_weekly_stats = [] # list to hold weekly Caseload statistics
    number_on_ta_wl = 0 # used to keep track of TA WL position
    number_on_pwp_wl = 0 # used to keep track of PwP WL position
    number_on_group_wl = 0 # used to keep track of groups WL position
    number_on_cbt_wl = 0 # used to keep track of CBT WL position
    number_on_couns_wl = 0 # used to keep track of Couns WL position

    # Caseload
    number_on_pwp_cl = 0 # used to keep track of PwP caseload
    number_on_group_cl = 0 # used to keep track of groups caseload
    number_on_cbt_cl = 0 # used to keep track of CBT caseload
    number_on_couns_cl = 0 # used to keep track of Couns caseload

    # bring in past referral data
    referral_rate_lookup = pd.read_csv('talking_therapies_referral_rates.csv'
                                                                ,index_col=0)
    #print(referral_rate_lookup)

# Patient to capture flow of patient through pathway
class Patient:
    def __init__(self, p_id):
        # Patient
        self.id = p_id
        self.patient_at_risk = 0 # used to determine DNA/Canx policy to apply

        self.week_added = None # Week they were added to the waiting list (for debugging purposes)

        # Referral
        self.referral_rejected = 0 # were they rejected at referral
        self.referral_time_screen = 0 # time taken to screen referral
        self.referral_req_review = 0 # does the ref need to go to MDT review
        self.time_to_mdt = 0 # how long to MDT, max 2 weeks
        self.opted_in = 0 # did the patient opt in or not
        self.opt_in_wait = 0 # how much of 1 week opt-in window was used
        self.opt_in_qtime = 0 # how much of 4 week TA app window was used
        self.attended_ta = 0 # did the patient attend TA appointment

        self.initial_step = [] # string, whether they were step 2 or step 3

        # Step2
        self.step2_resource_id = [] # identifier for the staff member allocated to their treatment
        self.step2_path_route = [] # string, which Step2 path they took
        self.step2_place_on_wl = 0 # position they are on Step2 waiting list
        self.step2_start_week = 0 # the week number they started treatment
        self.step2_session_count = 0 # counter for no. of sessions have had
        self.step2_drop_out = 0 # did they drop out during Step2
        self.step2_week_number = 0 # counter for which week number they are on
        self.step2_end_week = 0 # the week number when they completed treatment

        # Step3
        self.step3_resource_id = [] # identifier for the staff member allocated to their treatment
        self.step3_path_route = [] # string, which Step2 path they took
        self.step3_place_on_wl = 0 # position they are on Step2 waiting list
        self.step3_start_week = 0
        self.step3_session_count = 0 # counter for no. of sessions have had
        self.step3_drop_out = 0 # did they drop out during Step2
        self.step3_week_number = 0 # counter for which week number they are on
        self.step3_end_week = 0

# Staff class to be run weekly by week runner to record staff non-clinical time
class Staff:
    def __init__(self, s_id):

        # Staff attributes
        self.id = s_id
        self.week_number = 0 # the week number the staff activity is being recorded for
        self.staff_type = [] # what type of staff i.e. CBT, PwP, Couns
        self.staff_hours_avail = 0 # how many hours p/w they work
        self.staff_band = 0 # what staff band

        self.staff_time_wellbg = 0 # staff time for wellbeing
        self.staff_time_superv = 0 # staff time for supervision
        self.staff_time_breaks = 0 # staff time for breaks
        self.staff_time_huddle = 0 # staff time for counsellor huddle
        self.staff_time_cpd = 0 # staff time for CPD

class Model:
# Constructor to set up the model for a run. We pass in a run number when
# we create a new model
    def __init__(self, run_number):
        # Create a SimPy environment in which everything will live
        self.env = simpy.Environment()

        # # Create counters for various metrics we want to record
        self.patient_counter = 0
        self.run_number = run_number

        # Create a new DataFrame that will store opt-in results against the patient ID
        self.asst_results_df = pd.DataFrame()
        # Patient
        self.asst_results_df['Patient ID'] = [1]
        # Referral
        self.asst_results_df['Week Number'] = [0]
        self.asst_results_df['Run Number'] = [0]
        self.asst_results_df['At Risk'] = [0] # denotes at risk patient, 1 = Yes, 0 = No
        self.asst_results_df['Referral Time Screen'] = [0.0] # time in mins taken to screen referral
        self.asst_results_df['Referral Rejected'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Referral Reviewed'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Review Wait'] = [0.0] # time between screening and getting review
        self.asst_results_df['Review Rejected'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Opted In'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Opt-in Wait'] = [0.0] # time between opt-in notification and patient opting in
        self.asst_results_df['Opt-in Q Time'] = [0.0] # time between opting in and actual TA, 4 week window
        self.asst_results_df['TA Q Time'] = [0.0] # time spent queueing for TA
        self.asst_results_df['TA WL Posn'] = [0] # position in queue for TA
        self.asst_results_df['TA Outcome'] = [0] # 1 = Accepted, 0 = Rejected
        self.asst_results_df['TA Mins'] = [0] # time allocated to completing TA
        self.asst_results_df['Treatment Path'] = ['NA']

        # Indexing
        self.asst_results_df.set_index("Patient ID", inplace=True)

        # Step2
        # Create a new DataFrame that will store opt-in results against the patient ID
        self.step2_results_df = pd.DataFrame()

        self.step2_results_df['Patient ID'] = [1]
        self.step2_results_df['Week Number'] = [0]
        self.step2_results_df['Run Number'] = [0]
        self.step2_results_df['Step2 Route'] = ['NA'] # which Step2 pathway the patient was sent down
        self.step2_results_df['PwP WL Posn'] = [0] # place in queue for PwP
        self.step2_results_df['PwP Q Time'] = [0.0] # time spent queueing for PwP
        self.step2_results_df['Group WL Posn'] = [0] # place in queue for Group
        self.step2_results_df['Group Q Time'] = [0.0] # time spent queueing for Group
        self.step2_results_df['Session Number'] = [0]
        self.step2_results_df['Session Time'] = [0] # clinical session time in mins
        self.step2_results_df['Admin Time'] = [0] # admin session time in mins
        self.step2_results_df['IsDNA'] = [0]
        self.step2_results_df['IsDropout'] = [0]
        self.step2_results_df['Caseload'] = [0]
        self.step2_results_df['IsStepUp'] = [0] # was the patent stepped down

        # Indexing
        self.step2_results_df.set_index("Patient ID", inplace=True)

        # Step3
        # Create a new DataFrame that will store Step3 results against the patient ID
        # Create a new DataFrame that will store opt-in results against the patient ID
        self.step3_results_df = pd.DataFrame()

        self.step3_results_df['Patient ID'] = [1]
        self.step3_results_df['Week Number'] = [0]
        self.step3_results_df['Run Number'] = [0]
        self.step3_results_df['Step3 Route'] = ['NA'] # which Step2 pathway the patient was sent down
        self.step3_results_df['CBT WL Posn'] = [0] # place in queue for CBT
        self.step3_results_df['CBT Q Time'] = [0.0] # time spent queueing for CBT
        self.step3_results_df['Couns WL Posn'] = [0] # place in queue for Couns
        self.step3_results_df['Couns Q Time'] = [0.0] # time spent queueing for Couns
        self.step3_results_df['Session Number'] = [0]
        self.step3_results_df['Session Time'] = [0.0]
        self.step3_results_df['Admin Time'] = [0] # admin session time in mins
        self.step3_results_df['IsDNA'] = [0]
        self.step3_results_df['IsDropout'] = [0]
        self.step3_results_df['Caseload'] = [0]
        self.step3_results_df['IsStepDown'] = [0] # was the patent stepped down

        # Indexing
        self.step3_results_df.set_index("Patient ID", inplace=True)

        # Staff
        # staff counters separated by 100 to ensure no overlap in staff ID's when recording
        self.pwp_staff_counter = 100
        #self.group_staff_counter = 200 # not needed as covered by PwP
        self.cbt_staff_counter = 200
        self.couns_staff_counter = 300

        self.staff_results_df = pd.DataFrame()

        self.staff_results_df['Staff ID'] = [1]
        self.staff_results_df['Week Number'] = [0]
        self.staff_results_df['Run Number'] = [0]
        self.staff_results_df['Job Role'] = ['NA']
        self.staff_results_df['Supervision Mins'] = [0]
        self.staff_results_df['Break Mins'] = [0]
        self.staff_results_df['Wellbeing Mins'] = [0]
        self.staff_results_df['Huddle Mins'] = [0]
        self.staff_results_df['CPD Mins'] = [0]

        self.staff_results_df.set_index("Staff ID", inplace=True)

    # random number generator for activity times
    def random_normal(self, mean, std_dev):
        while True:
            activity_time = random.gauss(mean, std_dev)
            if activity_time > 0:
                return activity_time

    def week_runner(self,number_of_weeks):

        # week counter
        self.week_number = 0

        # list to hold each weekly amount of referrals
        self.referrals_generated = []
        # list to hold weekly asst statistics
        self.asst_weekly_stats = []
        # list to hold weekly Step2 statistics
        self.step2_weekly_stats = []
        # list to hold weekly Step3 statistics
        self.step3_weekly_stats = []
        # list to hold weekly Staff statistics
        self.staff_weekly_stats = []
        

        ######### Create our weekly resources #########
        self.ta_res = simpy.Container(
            self.env,capacity=g.ta_resource,
            init=g.ta_resource
            )
        
        self.group_res = simpy.Container(
            self.env,
            capacity=g.group_resource,
            init=g.group_resource
            )
        
        # Start up the referral generator function
        self.env.process(self.generator_patient_referrals())
        
        while self.week_number <= number_of_weeks:
            if g.debug_level >= 1:
                print(
                    f"""
##################################
# Week {self.week_number}
##################################
                    """
                    )

            # start up the staff entity generator
            self.env.process(self.staff_entity_generator(self.week_number))
            
            ##### record all weekly results #####
            ## Screening & TA
            self.asst_tot_screen = self.asst_results_df[
                                                'Referral Time Screen'].sum()
            self.asst_tot_reject = self.asst_results_df[
                                                'Referral Rejected'].sum()
            self.asst_optin_delay = self.asst_results_df['Opt-in Wait'].mean()
            self.asst_tot_optin = self.asst_results_df['Opted In'].sum()
            self.asst_optin_wait = self.asst_results_df['Opt-in Q Time'].mean()
            self.asst_tot_accept = self.asst_results_df['TA Outcome'].sum()

            self.asst_weekly_stats.append(
                {
                 'Week Number':self.week_number,
                 'Referral Screen Mins':self.asst_tot_screen,
                 'Referrals Rejected':self.asst_tot_reject,
                 'Referrals Delay Opt-in':self.asst_optin_delay,
                 'Referrals Opted-in':self.asst_tot_optin,
                 'Referrals Wait Opt-in':self.asst_optin_wait,
                 'TA Total Accept':self.asst_tot_accept
                }
                )
            
            ## Step2
            self.step2_route_list = ['PwP','Group']
            # create summary stats for each of the Step2 routes
            for i, route_name in enumerate(self.step2_route_list):
                # filter data for appropriate route
                self.step2_results_df_filtered = self.step2_results_df[
                                        self.step2_results_df["Step2 Route"]==route_name]
                # filter data to remove default rows
                # self.step2_results_df_filtered = self.step2_results_df_filtered[
                #                         self.step2_results_df_filtered["Step2 Route"]!='NA']
                
                ## Step2
                self.step2_route = route_name
                if route_name == 'PwP':
                    self.step2_max_wl = g.number_on_pwp_wl
                else:
                    self.step2_max_wl = g.number_on_group_wl
                if route_name == 'PwP':
                    self.step2_avg_wait = self.step2_results_df_filtered["PwP Q Time"].mean()
                else:
                    self.step2_avg_wait = self.step2_results_df_filtered["Group Q Time"].mean()
                self.step2_tot_clin = self.step2_results_df_filtered['Session Time'].sum()
                self.step2_tot_admin = self.step2_results_df_filtered['Admin Time'].sum()
                self.step2_tot_sess = self.step2_results_df_filtered['Session Number'].count()
                self.step2_tot_dna = self.step2_results_df_filtered['IsDNA'].sum()
                self.step2_tot_dropout = self.step2_results_df_filtered['IsDropout'].sum()
                self.step2_tot_complete = self.step2_results_df_filtered['IsDropout'
                                            ].count()-self.step2_results_df_filtered[
                                            'IsDropout'].sum()
                if route_name == 'PwP':
                    self.step2_tot_caseload = g.number_on_pwp_cl
                else:
                    self.step2_tot_caseload = g.number_on_group_cl
                # weekly Step2 Activity
                self.step2_weekly_stats.append(
                    {
                    'Route Name':self.step2_route,
                    'Week Number':self.week_number,
                    'Step2 WL':self.step2_max_wl,
                    'Step2 Q Time':self.step2_avg_wait,
                    'Step2 Clin Mins':self.step2_tot_clin,
                    'Step2 Admin Mins':self.step2_tot_admin,
                    'Step2 Sessions':self.step2_tot_sess,
                    'Step2 DNAs':self.step2_tot_dna,
                    'Step2 Dropout':self.step2_tot_dropout,
                    'Step2 Complete':self.step2_tot_complete,
                    'Step2 Caseload':self.step2_tot_caseload
                    }
                    )
            
            ## Step3
            self.step3_route_list = ['CBT','Couns']
            # create summary stats for each of the Step3 routes
            for i, route_name in enumerate(self.step3_route_list):
                # filter data for appropriate route
                self.step3_results_df_filtered = self.step3_results_df[
                                        self.step3_results_df["Step3 Route"]==route_name]

                # filter data to remove default rows
                self.step3_results_df_filtered = self.step3_results_df_filtered[
                                        self.step3_results_df_filtered["Step3 Route"]!='NA']
                
                ## Step3
                self.step3_route = route_name
                if route_name == 'CBT':
                    self.step3_max_wl = g.number_on_cbt_wl
                else:
                    self.step3_max_wl = g.number_on_couns_wl
                if route_name == 'CBT':
                    self.step3_avg_wait = self.step3_results_df_filtered["CBT Q Time"].mean()
                else:
                    self.step3_avg_wait = self.step3_results_df_filtered["Couns Q Time"].mean()
                self.step3_tot_clin = self.step3_results_df_filtered['Session Time'].sum()
                self.step3_tot_admin = self.step3_results_df_filtered['Admin Time'].sum()
                self.step3_tot_sess = self.step3_results_df_filtered['Session Number'].count()
                self.step3_tot_dna = self.step3_results_df_filtered['IsDNA'].sum()
                self.step3_tot_dropout = self.step3_results_df_filtered['IsDropout'].sum()
                self.step3_tot_complete = self.step3_results_df_filtered['IsDropout'
                                            ].count()-self.step3_results_df_filtered[
                                            'IsDropout'].sum()
                if route_name == 'CBT':
                    self.step3_tot_caseload = g.number_on_cbt_cl
                else:
                    self.step3_tot_caseload = g.number_on_couns_cl
                # weekly Step3 Activity
                self.step3_weekly_stats.append(
                    {
                    'Route Name':self.step3_route,
                    'Week Number':self.week_number,
                    'Step3 WL':self.step3_max_wl,
                    'Step3 Q Time':self.step3_avg_wait,
                    'Step3 Clin Mins':self.step3_tot_clin,
                    'Step3 Admin Mins':self.step3_tot_admin,
                    'Step3 Sessions':self.step3_tot_sess,
                    'Step3 DNAs':self.step3_tot_dna,
                    'Step3 Dropout':self.step3_tot_dropout,
                    'Step3 Complete':self.step3_tot_complete,
                    'Step3 Caseload':self.step3_tot_caseload
                    }
                    )
            
            ## Staff
            self.job_role_list = ['PwP','CBT','Couns']
            # create summary stats for each of the job roles
            for i, job_role in enumerate(self.job_role_list):
                # filter data for appropriate route
                self.staff_results_df_filtered = self.staff_results_df[
                                        self.staff_results_df["Job Role"]==job_role]
            
                self.job_role_name = job_role
                
                self.staff_tot_superv = self.staff_results_df_filtered['Supervision Mins'].sum()
                self.staff_tot_break = self.staff_results_df_filtered['Break Mins'].sum()
                self.staff_tot_wellb = self.staff_results_df_filtered['Wellbeing Mins'].sum()
                self.staff_tot_huddle = self.staff_results_df_filtered['Huddle Mins'].sum()
                self.staff_tot_cpd = self.staff_results_df_filtered['CPD Mins'].sum()
 
                # weekly staff non-clinical activity
                self.staff_weekly_stats.append(
                    {
                    'Job Role':self.job_role_name,
                    'Week Number':self.week_number,
                    'Supervision Mins':self.staff_tot_superv,
                    'Break Mins':self.staff_tot_break,
                    'Wellbeing Mins':self.staff_tot_wellb,
                    'Huddle Mins':self.staff_tot_huddle,
                    'CPD Mins':self.staff_tot_cpd
                    }
                    )
                
            ##### Take a snapshot of the weekly caseload levels #####
            
            self.weekly_pwp_snapshot = {'Run Number':self.run_number
                                       ,'Week Number':self.week_number
                                       ,'Data':[]}
            
            for pwp_caseload_id, pwp_level in self.pwp_resources.items():
                self.weekly_pwp_snapshot['Data'].append({
                                            'Caseload ID':pwp_caseload_id
                                            ,'Caseload Level':pwp_level.level})
            
            g.caseload_weekly_stats.append(self.weekly_pwp_snapshot)
                
            self.weekly_cbt_snapshot = {'Run Number':self.run_number
                                       ,'Week Number':self.week_number
                                       ,'Data':[]}
            
            for cbt_caseload_id, cbt_level in self.cbt_resources.items():
                self.weekly_cbt_snapshot['Data'].append({
                                            'Caseload ID':cbt_caseload_id
                                            ,'Caseload Level':cbt_level.level})
            
            g.caseload_weekly_stats.append(self.weekly_cbt_snapshot)
            
            self.weekly_couns_snapshot = {'Run Number':self.run_number
                                       ,'Week Number':self.week_number
                                       ,'Data':[]}
            
            for couns_caseload_id, couns_level in self.couns_resources.items():
                self.weekly_couns_snapshot['Data'].append({
                                            'Caseload ID':couns_caseload_id
                                            ,'Caseload Level':couns_level.level})
                
            g.caseload_weekly_stats.append(self.weekly_couns_snapshot)

            ######### replenish resources ##########
            if g.debug_level >= 2:
                print("")
                print("== Replenishing Resources==")

            ##### TA #####
            ta_amount_to_fill = g.ta_resource - self.ta_res.level
            # pwp_amount_to_fill = g.pwp_resource - self.pwp_res.level
            group_amount_to_fill = g.group_resource - self.group_res.level
            
            if ta_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"TA Level: {self.ta_res.level}")
                    print(f"Putting in {ta_amount_to_fill}")

                self.ta_res.put(ta_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New TA Level: {self.ta_res.level}")

            if group_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"Group Level: {self.group_res.level}")
                    print(f"Putting in {group_amount_to_fill}")

                self.group_res.put(group_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New Group Level: {self.group_res.level}")

            # Wait one unit of simulation time (1 week)
            yield(self.env.timeout(1))

            if g.debug_level >= 1:
                print(
                    f"""

#----------------------------------
# Week {self.week_number} Complete
#----------------------------------

                    """
                    )

            # increment week number by 1 week
            self.week_number += 1

        self.referral_gen_complete = True # determines whether the referral generator has finished running

    ##### generator function that represents the DES generator for referrals
    def generator_patient_referrals(self):

        # tracks whcih week number we are on
        self.referral_week_number = 0

        while self.referral_week_number < g.sim_duration:
            # get the number of referrals that week based on the mean + seasonal variance
            self.referrals_this_week = round(g.mean_referrals_pw +
                                        (g.mean_referrals_pw *
                                        g.referral_rate_lookup.at[
                                        self.referral_week_number+1,'PCVar'])) # weeks start at 1

            # print(f"Referrals generated this week: {self.referrals_this_week}")

            # print(self.referrals_this_week)

            if g.debug_level >= 1:
                print(f'Week {self.referral_week_number}: {self.referrals_this_week}'
                                                        ' referrals generated')
                print('')
                
            # append referrals to the list ready for processing
            self.referrals_generated.append(self.referrals_this_week)
            # add them to the tracker so we know how many referrals/patients need processing in total for the whole sim run
            self.referral_tracker += self.referrals_this_week
            # increment the referral week number by 1
            self.referral_week_number += 1
            
        ##### Now that the referrals for the sim duration have been generated, process them in weekly batches
        
        # keep running until all patients have been processed
        while self.referral_tracker > 0:

            self.patient_week_number = 0
            # do this for however many weeks there are in the sim_duration
            while self.patient_week_number < g.sim_duration:

                # get the number of referrals at this week number position in the list
                self.referrals_this_week = self.referrals_generated[self.patient_week_number]
                # start the referral counter
                self.referral_counter = 0

                # run this for as many times as there are referrals for that week
                while self.referral_counter <= self.referrals_this_week:
                
                    # increment the referral counter by 1
                    self.referral_counter += 1

                    # run the asst pathway generator for this referral and pass it the 
                    self.env.process(self.patient_asst_pathway(self.referral_week_number))

                # reset the referral counter ready for the next batch
                self.referral_counter = 0
                # increment the referral week number by 1
                self.patient_week_number += 1
                # wait 1 unit of time i.e. 1 week
                yield(self.env.timeout(1))

            self.patient_week_number = 0

    # this function builds staff resources containing the number of slots on the caseload
    def resource_builder(self):

        ##### PwP #####
        self.p_type = 'PwP'
        # dictionary to hold PwP caseload resources
        self.pwp_resources = {f'{self.p_type}_{p}':simpy.Container(self.env,
                    capacity=g.pwp_caseload,
                    init=g.pwp_caseload) for p in range(g.number_staff_pwp)}
            # caseload counter for each CBT resource
        
        # dictionary to hold PwP resource caseload levels
        #self.pwp_caseloads = {f'{self.p_type}_{p}': 0 for p in range(g.number_staff_pwp)}
            
        ##### CBT #####
        self.c_type = 'CBT'
        # dictionary to hold CBT caseload resources
        self.cbt_resources = {f'{self.c_type}_{c}':simpy.Container(self.env,
                    capacity=g.cbt_caseload,
                    init=g.cbt_caseload) for c in range(g.number_staff_cbt)}
            
        # dictionary to hold CBT resource caseload levels
        #self.cbt_caseloads = {f'{self.c_type}_{c}': 0 for c in range(g.number_staff_cbt)}
        
        ##### Couns #####
        self.s_type = 'Couns'
        # dictionary to hold Couns caseload resources
        self.couns_resources = {f'{self.s_type}_{s}':simpy.Container(self.env,
                    capacity=g.couns_caseload,
                    init=g.couns_caseload) for s in range(g.number_staff_couns)}
                    
        # dictionary to hold Couns resource caseload levels
        #self.couns_caseloads = {f'{self.s_type}_{c}': 0 for c in range(g.number_staff_couns)}

        yield(self.env.timeout(0))

    def find_caseload_slot(self,r_type):

        # load in the right resource dictionary
        if r_type == 'PwP':
            self.resources = self.pwp_resources
        elif r_type == 'CBT':
            self.resources = self.cbt_resources
        elif r_type == 'Couns':
            self.resources = self.couns_resources

        while True:
            # Iterate over the resources to check if any have a level > 0
            for self.resource_name, self.container in self.resources.items():
                if self.container.level > 0:
                    if g.debug_level >=2:
                        print(f'Resource {self.resource_name} with a caseload of {self.container.level} selected')
                    return self.resource_name, self.container  # Return the label and the container if available

            # If no resource is available, wait and check again
            yield self.env.timeout(0)
                    
    ###### generator for staff to record non-clinical activity #####
    def staff_entity_generator(self, week_number):

        yield self.env.process(self.pwp_staff_generator(week_number))
        # self.env.process(self.group_staff_generator(week_number)) # not needed as covered by pwp
        yield self.env.process(self.cbt_staff_generator(week_number))
        yield self.env.process(self.couns_staff_generator(week_number))

        yield(self.env.timeout(0))

    def pwp_staff_generator(self,week_number):

        self.pwp_counter = 0
       
        # iterate through the PwP staff accounting for half WTE's
        # counter only increments by 0.5 so in effect each staff member
        # will get processed twice each week
        while self.pwp_counter < g.number_staff_pwp:

            # Increment the staff counter by 0.5
            self.pwp_counter += 0.5

            # Create a new staff member from Staff Class
            s = Staff(self.pwp_staff_counter+(self.pwp_counter*2))

            if g.debug_level >=2:
                print('')
                print(f"==== PwP Staff {s.id} Generated ====")
            
            self.staff_results_df.at[s.id,'Week Number'] = week_number
            self.staff_results_df.at[s.id,'Run Number'] = self.run_number
            self.staff_results_df.at[s.id,'Job Role'] = 'PwP'
            self.staff_results_df.at[s.id,'Break Mins'] = g.break_time/2
            #self.staff_results_df.at[s.id,'Huddle Mins'] = g.huddle_time # counsellors only
            
            # monthly staff activities
            if self.week_number % 4 == 0:
                
                self.staff_results_df.at[s.id,'Supervision Mins'] = g.supervision_time/2
                self.staff_results_df.at[s.id,'Wellbeing Mins'] = g.wellbeing_time/2
                self.staff_results_df.at[s.id,'CPD Mins'] = g.cpd_time/2
        
        yield(self.env.timeout(0))
        
        # reset the staff counter back to original level once all staff have been processed
        self.pwp_staff_counter = 100

    def cbt_staff_generator(self,week_number):

        self.cbt_counter = 0
       
        # iterate through the CBT staff accounting for half WTE's
        # counter only increments by 0.5 so in effect each staff member
        # will get processed twice each week
        while self.cbt_counter < g.number_staff_cbt:

            # Increment the staff counter by 0.5
            self.cbt_counter += 0.5

            # Create a new staff member from Staff Class
            s = Staff(self.cbt_staff_counter+(self.cbt_counter*2))

            if g.debug_level >=2:
                print('')
                print(f"==== CBT Staff {s.id} Generated ====")
            
            self.staff_results_df.at[s.id,'Week Number'] = week_number
            self.staff_results_df.at[s.id,'Run Number'] = self.run_number
            self.staff_results_df.at[s.id,'Job Role'] = 'CBT'
            self.staff_results_df.at[s.id,'Break Mins'] = g.break_time/2
            #self.staff_results_df.at[s.id,'Huddle Mins'] = g.huddle_time # counsellors only
            
            # monthly staff activities
            if self.week_number % 4 == 0:
                
                self.staff_results_df.at[s.id,'Supervision Mins'] = g.supervision_time/2
                self.staff_results_df.at[s.id,'Wellbeing Mins'] = g.wellbeing_time/2
                self.staff_results_df.at[s.id,'CPD Mins'] = g.cpd_time/2
        
        yield(self.env.timeout(0))
        
        # reset the staff counter back to original level once all staff have been processed
        self.cbt_staff_counter = 200

    def couns_staff_generator(self,week_number):

        self.couns_counter = 0
       
        # iterate through the Couns staff accounting for half WTE's
        # counter only increments by 0.5 so in effect each staff member
        # will get processed twice each week
        while self.couns_counter < g.number_staff_couns:

            # Increment the staff counter by 0.5
            self.couns_counter += 0.5

            # Create a new staff member from Staff Class
            s = Staff(self.couns_staff_counter+(self.couns_counter*2))

            if g.debug_level >=2:
                print('')
                print(f"==== Couns Staff {s.id} Generated ====")
            
            self.staff_results_df.at[s.id,'Week Number'] = week_number
            self.staff_results_df.at[s.id,'Run Number'] = self.run_number
            self.staff_results_df.at[s.id,'Job Role'] = 'Couns'
            self.staff_results_df.at[s.id,'Break Mins'] = g.break_time/2
            self.staff_results_df.at[s.id,'Huddle Mins'] = g.counsellors_huddle/2 # Couns only
            
            # monthly staff activities
            if self.week_number % 4 == 0:
                
                self.staff_results_df.at[s.id,'Supervision Mins'] = g.supervision_time/2
                self.staff_results_df.at[s.id,'Wellbeing Mins'] = g.wellbeing_time/2
                self.staff_results_df.at[s.id,'CPD Mins'] = g.cpd_time/2
        
        yield(self.env.timeout(0))
        
        # reset the staff counter back to original level once all staff have been processed
        self.couns_staff_counter = 300

    ###### assessment part of the clinical pathway #####
    def patient_asst_pathway(self, week_number):

        # decide whether the referral was rejected at screening stage
        self.reject_referral = random.uniform(0,1)
        # decide whether the referral needs to go for review if not rejected
        self.requires_review = random.uniform(0,1)
        # decide whether the referral is rejected at review
        self.asst_review_reject = random.uniform(0,1)
            # decide whether the Patient opts-in
        self.patient_optedin = random.uniform(0,1)
        # decide whether the Patient is accepted following TA
        self.ta_accepted = random.uniform(0,1)

        # Increment the patient counter by 1
        self.patient_counter += 1

        # Create a new patient from Patient Class
        p = Patient(self.patient_counter)
        p.week_added = week_number
        
        if g.debug_level >=2:
                print('')
                print(f"==== Patient {p.id} Generated ====")

        # all referrals get screened
        self.asst_results_df.at[p.id, 'Referral Time Screen'
                                        ] = self.random_normal(
                                        g.referral_screen_time
                                        ,g.std_dev)

        #print(f'Week {week_number}: Patient number {p.id} created')

        # check whether the referral was a straight reject or not
        if self.reject_referral <= g.referral_rej_rate:

            # if this referral is rejected mark as rejected
            self.asst_results_df.at[p.id, 'Run Number'] = self.run_number

            self.asst_results_df.at[p.id, 'Week Number'] = self.week_number

            self.asst_results_df.at[p.id, 'Referral Rejected'] = 1

            if g.debug_level >=2:
                print(f"Patient {p.id} Rejected")

            # remove this patient from the sim
            self.referral_tracker -= 1

        else:

            self.asst_results_df.at[p.id, 'Run Number'] = self.run_number

            self.asst_results_df.at[p.id, 'Week Number'] = self.week_number
            # Mark referral as accepted and move on to whether it needs a review
            self.asst_results_df.at[p.id, 'Referral Rejected'] = 0

            print(f"Patient {p.id} Accepted")

            # Now decide whether the patient has previously been treated and needs to go for review
            if self.requires_review >= g.referral_review_rate and self.asst_review_reject <= g.review_rej_rate:
                
                self.asst_results_df.at[p.id, 'Review Rejected'] = 1
                
                if g.debug_level >=2:
                    print(f"Patient {p.id} Reviewed and Rejected at review")

                # set flag to show Patient required review
                self.asst_results_df.at[p.id, 'Referral Reviewed'] = 1
                # record how long they waited for MDT review between 0 and 2 weeks
                self.asst_results_df.at[p.id, 'Review Wait'] = random.uniform(0,
                                                                g.mdt_freq)
                # remove this patient from the sim
                self.referral_tracker -= 1
            
            # patient doesn't need a review or does and was accepted                                                  g.mdt_freq)
            else :
                # patient required a review and was accepted
                if self.requires_review >= g.referral_review_rate:
                    # set flag to show Patient required review
                    self.asst_results_df.at[p.id, 'Referral Reviewed'] = 1
                    # therefore no review wait
                    self.asst_results_df.at[p.id, 'Review Wait'] = random.uniform(0,
                                                                g.mdt_freq)
                    # set flag to show they were accepted and go to opt-in
                    self.asst_results_df.at[p.id, 'Review Rejected'] = 0
                    
                    if g.debug_level >=2:
                        print(f"Patient {p.id} Accepted at Review - go to opt-in")
                    
                else:
                    # patient didn't require a review
                    self.asst_results_df.at[p.id, 'Referral Reviewed'] = 0
                    # record how long they waited for MDT review between 0 and 2 weeks
                    self.asst_results_df.at[p.id, 'Review Wait'] = 0

                    if g.debug_level >=2:
                        print(f"Patient {p.id} did not require a Review - go to opt-in")

                # now we can carry on and decide whether the patient opted-in or not
                if self.patient_optedin >= g.opt_in_rate:
                    # set flag to show Patient failed to opt-in
                    self.asst_results_df.at[p.id, 'Opted In'] = 0
                    if g.debug_level >=2:
                        print(f"Patient {p.id} Failed to Opt In")
                    # therefore didn't wait to opt-in
                    self.asst_results_df.at[p.id, 'Opt-in Wait'] = 0
                    # and didn't queue for TA appt
                    self.asst_results_df.at[p.id, 'Opt-in Q Time'] = 0
                    # remove this patient from the sim
                    self.referral_tracker -= 1
                else:
                    # otherwise set flag to show they opted-in
                    self.asst_results_df.at[p.id, 'Opted In'] = 1
                    if g.debug_level >=2:
                        print(f"Patient {p.id} Opted In")
                    # record how long they took to opt-in, 1 week window
                    self.asst_results_df.at[p.id, 'Opt-in Wait'
                                                ] = random.uniform(0,1)
                    # record lag-time between opting in and TA appointment, max 4 week window
                    self.asst_results_df.at[p.id, 'Opt-in Q Time'
                                                ] = random.uniform(0,4)

                    start_q_ta = self.env.now

                    g.number_on_ta_wl += 1

                    # Record where the patient is on the TA WL
                    self.asst_results_df.at[p.id, "TA WL Posn"] = \
                                                        g.number_on_ta_wl

                    # Request a Triage resource from the container
                    with self.ta_res.get(1) as ta_req:
                        yield ta_req

                    #print(f'Patient {p} started TA')

                    # as each patient reaches this stage take them off TA wl
                    g.number_on_ta_wl -= 1

                    if g.debug_level >= 2:
                        print(f'Week {self.env.now}: Patient number {p.id} (added week {p.week_added}) put through TA')

                    end_q_ta = self.env.now

                    # Calculate how long patient queued for TA
                    self.q_time_ta = end_q_ta - start_q_ta
                    # Record how long patient queued for TA
                    self.asst_results_df.at[p.id, 'TA Q Time'] = self.q_time_ta

                    # Now do Telephone Assessment using mean and varying
                    self.asst_results_df.at[p.id, 'TA Mins'
                                                    ] = self.random_normal(
                                                    g.ta_time_mins
                                                    ,g.std_dev)
                    # decide if the patient is accepted following TA
                    if self.ta_accepted >= g.ta_accept_rate:
                        # Patient was rejected at TA stage
                        self.asst_results_df.at[p.id, 'TA Outcome'] = 0
                        if g.debug_level >=2:
                            print(f"Patient {p.id} Rejected at TA Stage")

                        # remove this patient from the sim
                        self.referral_tracker -= 1

                        # used to decide whether further parts of the pathway are run or not
                        self.ta_accepted = 0
                    else:
                        # Patient was accepted at TA stage
                        self.asst_results_df.at[p.id, 'TA Outcome'] = 1
                        if g.debug_level >=2:
                            print(f"Patient {p.id} Accepted at TA Stage")

                            # used to decide whether further parts of the pathway are run or not
                        self.ta_accepted = 1

                        if self.ta_accepted == 1 :

                            # if patient was accepted decide which pathway the patient has been allocated to
                            # Select 2 options based on the given probabilities
                            self.step_options = random.choices(g.step_routes, weights=g.step2_step3_ratio, k=self.referrals_this_week)

                            #print(self.selected_step)
                            self.selected_step = random.choice(self.step_options)

                            if self.selected_step == "Step3":
                                print(f"Selected step: **{self.selected_step}**")
                            else:
                                print(f"Selected step: {self.selected_step}")

                            self.asst_results_df.at[p.id, 'Treatment Path'] = self.selected_step
                            p.initial_step = self.selected_step

                            if g.debug_level >=2:
                                print(f"-- Pathway Runner Initiated --")
                            # proceed to next patient and run pathway runner
                            yield self.env.timeout(0)
                            self.env.process(self.pathway_runner(p))

                            #return self.asst_results_df

                        else:
                            # otherwise proceed to next patient
                            yield self.env.timeout(0)
        # print(self.asst_results_df)

    def pathway_runner(self, patient):

        p = patient

        if p.initial_step == 'Step2':
            print(f'PATHWAY RUNNER: Patient {p.id} sent down **{p.initial_step}** pathway')
            #yield self.env.timeout(0)
            yield self.env.process(self.patient_step2_pathway(p))
        else:
            print(f'PATHWAY RUNNER: Patient {p.id} sent down {p.initial_step} pathway')
            #yield self.env.timeout(0)
            yield self.env.process(self.patient_step3_pathway(p))

    ###### step2 pathway #####
    def patient_step2_pathway(self, patient):

        p = patient
        # Select one of 2 treatment options based on the given probabilities
        self.step2_pathway_options = random.choices(g.step2_routes,
                                                weights=g.step2_path_ratios,
                                                k=self.referrals_this_week)

        self.selected_step2_pathway = random.choice(self.step2_pathway_options)
        
        p.step2_path_route = self.selected_step2_pathway

        self.step2_results_df.at[p.id, 'Step2 Route'
                                            ] = p.step2_path_route

        # push the patient down the chosen step2 route
        if self.selected_step2_pathway == 'PwP':
            # add to PwP WL
            g.number_on_pwp_wl += 1
            yield self.env.timeout(0)
            self.env.process(self.step2_pwp_process(p))
        else:
            if g.debug_level >=2:
                print(f"Patient {p.id} sent to Group store")
            
                self.group_store.put(p)

                # add to group WL
                g.number_on_group_wl += 1

                if g.debug_level >=2:
                    print(f'Group store contains {len(self.group_store.items)} of possible {g.step2_group_size}')

                self.start_q_group = self.env.now

                if len(self.group_store.items) == 7:
                    if g.debug_level >=2:
                        print(f'Group is now full, putting {len(self.group_store.items)} through group therapy')
                    # put all the stored patients through group therapy
                    while len(self.group_store.items) > 0:

                        p = yield self.group_store.get()

                        if g.debug_level >=2:
                            print(f'Putting Patient {p.id} through Group Therapy, {len(self.group_store.items)} remaining')
                        if g.debug_level >=2:
                                print(f"FUNC PROCESS patient_step2_pathway: Patient {p.id} Initiating {p.step2_path_route} Step 2 Route")
                        yield self.env.timeout(0)
                        self.env.process(self.step2_group_process(p))

        #yield self.env.timeout(0)
            
    ###### step3 pathway #####
    def patient_step3_pathway(self, patient):

        p = patient
        # Select one of 2 treatment options based on the given probabilities
        self.step3_pathway_options = random.choices(g.step3_routes,
                                                weights=g.step3_path_ratios,
                                                k=self.referrals_this_week)

        self.selected_step3_pathway = random.choice(self.step3_pathway_options)

        p.step3_path_route = self.selected_step3_pathway

        self.step3_results_df.at[p.id, 'Step3 Route'
                                            ] = p.step3_path_route

        # push the patient down the chosen step2 route
        if self.selected_step3_pathway == 'CBT':
            # add to CBT WL
            g.number_on_cbt_wl += 1
            yield self.env.timeout(0)
            self.env.process(self.step3_cbt_process(p))
        else:
            # add to Couns WL
            g.number_on_couns_wl += 1
            yield self.env.timeout(0)
            self.env.process(self.step3_couns_process(p))
            
        if g.debug_level >=2:
                print(f"FUNC PROCESS patient_step3_pathway: Patient {p.id} Initiating {p.step3_path_route} Step 3 Route")

        #yield self.env.timeout(0)

    def step2_pwp_process(self,patient):

        p = patient

        # counter for number of group sessions
        self.pwp_session_counter = 0
        # counter for applying DNA policy
        self.pwp_dna_counter = 0

        if g.debug_level >=2:
            print(f'{p.step2_path_route} RUNNER: Patient {p.id} added to {p.step2_path_route} waiting list')

        start_q_pwp = self.env.now

        # Record where the patient is on the TA WL
        self.step2_results_df.at[p.id, 'PwP WL Posn'] = \
                                            g.number_on_pwp_wl

        # Check if there is a caseload slot available and return the resource
        result = yield self.env.process(self.find_caseload_slot('PwP'))

        # Safeguard unpacking: Ensure result is not None and has two elements
        if result:
            self.pwp_caseload_id, self.pwp_caseload_res = result
        else:
            # Handle the case where no resource was available (shouldn't happen as function keeps checking)
            print("No available resource found!")
            
        if g.debug_level >=2:
            print(f'Resource {self.pwp_caseload_id} with a caseload remaining of {self.pwp_caseload_res.level} allocated to patient {p.id}')
        
        with self.pwp_caseload_res.get(1) as self.pwp_req:
            yield self.pwp_req

        # # create a variable to store the current level of the caseload for this resource
        # self.pwp_caseload_posn = self.caseload_[f'{self.caseload_id}']
        # # add to this specific caseload
        # self.pwp_caseload_posn +=1

        if g.debug_level >=2:
            print(f'Patient {p.id} added to caseload {self.pwp_caseload_id},{self.pwp_resources[self.pwp_caseload_id].level} spaces left')

        # add to caseload
        g.number_on_pwp_cl += 1
        
        # as each patient reaches this stage take them off PwP wl
        g.number_on_pwp_wl -= 1

        if g.debug_level >=2:
            print(f'{p.step2_path_route} RUNNER: Patient {p.id} removed from {p.step2_path_route} waiting list')

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step2_pwp_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) put through {p.step2_path_route}')

        end_q_pwp = self.env.now

        p.step2_start_week = self.week_number

        # Calculate how long patient queued for TA
        self.q_time_pwp = end_q_pwp - start_q_pwp
        # Record how long patient queued for TA
        self.asst_results_df.at[p.id, 'PwP Q Time'] = self.q_time_pwp

        # Generate a list of week numbers the patient is going to attend
        self.pwp_random_weeks = random.sample(range(self.week_number+1, self.week_number+g.step2_pwp_period), g.step2_pwp_sessions)

        # Add 1 at the start of the list
        self.pwp_random_weeks.insert(0, 0)

        # Optionally, sort the list to maintain sequential order
        self.pwp_random_weeks.sort()

        # print(self.random_weeks)

        while self.pwp_session_counter < g.step2_pwp_sessions and self.pwp_dna_counter < 2:

            if g.debug_level >= 2:
                print(f'FUNC PROCESS step2_pwp_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) on {p.step2_path_route} Session {self.pwp_session_counter} on Week {self.week_number + self.pwp_random_weeks[self.pwp_session_counter]}')

            # increment the pwp session counter by 1
            self.pwp_session_counter += 1

            # record the pwp session number for the patient
            self.step2_results_df.at[p.id, 'Session Number'] = self.pwp_session_counter

            
            # record stats for the patient against this session number
            self.step2_results_df.at[p.id,'Patient ID'] = p
            self.step2_results_df.at[p.id,'Week Number'] = self.week_number + self.pwp_random_weeks[self.pwp_session_counter]
            self.step2_results_df.at[p.id,'Run Number'] = self.run_number
            self.step2_results_df.at[p.id, 'Treatment Route'
                                                ] = p.step2_path_route
            
            # decide whether the patient was stepped up 
            self.step_patient_up = random.uniform(0,1)
            # is the patient approaching the end of treatment and do they need to be stepped up?
            if self.pwp_session_counter >= g.step2_pwp_sessions-1 and self.step_patient_up <= g.step_up_rate:
                
                self.step2_results_df['IsStepUp'] = 1
                if g.debug_level >= 2:
                    print(f'### STEPPED UP ###: Patient {p.id} has been stepped up, running Step3 route selector')
                yield(self.env.timeout(0))
                self.env.process(self.patient_step3_pathway(p))
            else:
                self.step2_results_df['IsStepUp'] = 0

            # decide whether the session was DNA'd
            self.dna_pwp_session = random.uniform(0,1)

            if self.dna_pwp_session <= g.step2_pwp_dna_rate:
                self.step2_results_df.at[p.id, 'IsDNA'] = 1
                self.pwp_dna_counter += 1
                # if session is DNA just record admin mins as clinical time will be used elsewhere
                self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin
                if g.debug_level >= 2:
                    print(f'Patient {p.id} on {p.step2_path_route} Session '
                           f'{self.pwp_session_counter} DNA number ' 
                           f'{self.pwp_dna_counter}')
                
            else:
                self.step2_results_df.at[p.id, 'IsDNA'] = 0
                if self.pwp_session_counter == 1:
                    # if it's the 1st session use 1st session time
                    self.step2_results_df.at[p.id,'Session Time'] = g.step2_pwp_1st_mins
                    self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin
                else:
                    # otherwise use follow-up session time
                    self.step2_results_df.at[p.id,'Session Time'] = g.step2_pwp_fup_mins
                    self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin

        # record whether patient dropped out before completing pwP
        if self.pwp_dna_counter >= 2:
            self.step2_results_df.at[p.id, 'IsDropOut'] = 1
            if g.debug_level >= 2:
                print(f'Patient {p.id} dropped out of {p.step2_path_route} treatment')
            p.step2_end_week = p.step2_start_week+self.pwp_random_weeks[self.pwp_session_counter]
        else:
            self.step2_results_df.at[p.id, 'IsDropOut'] = 0
            if g.debug_level >= 2:
                print(f'Patient {p.id} completed {p.step2_path_route} treatment')
            p.step2_end_week = p.step2_start_week+max(self.pwp_random_weeks)

        # remove from Step 2 Caseload as have either completed treatment or dropped out
        self.step2_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for pwp sessions
        self.pwp_session_counter = 0
        self.pwp_dna_counter = 0

        # remove from overall caseload
        g.number_on_pwp_cl -=1

        # # remove from this specific caseload
        # self.pwp_caseload_posn -=1

        # Return PwP caseload resource to the container
        with self.pwp_caseload_res.put(1) as pwp_rel:
            yield pwp_rel

        if self.pwp_dna_counter >= 2:
            # if patient dropped out hold onto the resource latest attended session
            yield self.env.timeout(self.pwp_random_weeks[self.pwp_session_counter])
            if g.debug_level >= 2:
                print(f'Patient {p.id} starting at week {p.step2_start_week} discharged from {p.step2_path_route} at week {p.step2_end_week}')
        else:
            # otherwise hold onto the resource until the last session
            yield self.env.timeout(max(self.pwp_random_weeks))
            if g.debug_level >= 2:
                print(f'Patient {p.id} starting at week {p.step2_start_week} discharged from {p.step2_path_route} at week {p.step2_end_week}')

        # remove this patient from the sim
        self.referral_tracker -= 1
    
    def step2_group_process(self,patient):

        p = patient

        # counter for number of group sessions
        self.group_session_counter = 0
        # counter for applying DNA policy
        self.group_dna_counter = 0

        # Record where the patient is on the TA WL
        self.step2_results_df.at[p.id, 'Group WL Posn'] = \
                                            g.number_on_group_wl

        # Request a Group resource from the container
        with self.group_res.get(1) as group_req:
            yield group_req

        # add to caseload
        g.number_on_group_cl +=1

        # print(f'Patient {p} started PwP')

        # as each patient reaches this stage take them off Group wl
        g.number_on_group_wl -= 1

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step2_group_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) put through {p.step2_path_route}')

        self.end_q_group = self.env.now

        # Calculate how long patient queued for groups
        self.q_time_group = self.end_q_group - self.start_q_group
        # Record how long patient queued for groups
        self.asst_results_df.at[p.id, 'Group Q Time'] = self.q_time_group

        while self.group_session_counter < g.step2_group_sessions and self.group_dna_counter < 2:
            if g.debug_level >= 2:
                print(f'Week {self.env.now+self.group_session_counter}: Patient {p.id} (added week {p.week_added}) on {p.step2_path_route} Session {self.group_session_counter}')

            # increment the group session counter by 1
            self.group_session_counter += 1

            # record the session number for the patient
            self.step2_results_df.at[p.id, 'Session Number'] = self.group_session_counter
            # mark patient as still on Step2 Caseload
            self.step2_results_df.at[p.id, 'Caseload'] = 1

            # record stats for the patient against this session number
            self.step2_results_df.at[p.id,'Patient ID'] = p
            # artificially increase the week number so it reports as consecutive weeks not same week
            self.step2_results_df.at[p.id,'Week Number'] = self.env.now+self.group_session_counter
            self.step2_results_df.at[p.id,'Run Number'] = self.run_number
            self.step2_results_df.at[p.id,'Treatment Route'
                                                ] = p.step2_path_route
            
            # decide whether the session was DNA'd
            self.dna_group_session = random.uniform(0,1)

            if self.dna_group_session <= g.step2_group_dna_rate:
                self.step2_results_df.at[p.id, 'IsDNA'] = 1
                self.group_dna_counter += 1
                self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin
                if g.debug_level >= 2:
                    print(f'Patient {p.id} on {p.step2_path_route} ' 
                          f'Session {self.group_session_counter} DNA number ' 
                          f'{self.group_dna_counter}')
            
            else:
                self.step2_results_df.at[p.id, 'IsDNA'] = 0
                self.step2_results_df.at[p.id,'Session Time'] = g.step2_group_session_mins
                self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin

        # record whether patient dropped out before completing Wellbeing Workshop
        if self.group_dna_counter >= 2:
            self.step2_results_df.at[p.id, 'IsDropOut'] = 1
            if g.debug_level >= 2:
                print(f'Patient {p.id} dropped out of {p.step2_path_route} treatment')
        else:
            self.step2_results_df.at[p.id, 'IsDropOut'] = 0
            if g.debug_level >= 2:
                print(f'Patient {p.id} completed {p.step2_path_route} treatment')
        # remove from Step 2 Caseload as have either completed treatment or dropped out
        self.step2_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for group sessions
        self.group_session_counter = 0
        self.group_dna_counter = 0

        # remove from overall caseload
        g.number_on_group_cl -=1

        # remove this patient from the sim
        self.referral_tracker -= 1

        yield self.env.timeout(self.group_session_counter)
        
    def step3_cbt_process(self,patient):

        p = patient

        # counter for number of cbt sessions
        self.cbt_session_counter = 0
        # counter for applying DNA policy
        self.cbt_dna_counter = 0

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} added to {p.step3_path_route} waiting list')

        start_q_cbt = self.env.now

        # Record where the patient is on the cbt WL
        self.step3_results_df.at[p.id, 'CBT WL Posn'] = \
                                            g.number_on_cbt_wl

        # Check if there is a caseload slot available and return the resource
        result = yield self.env.process(self.find_caseload_slot('CBT'))

        # Safeguard unpacking: Ensure result is not None and has two elements
        if result:
            self.cbt_caseload_id, self.cbt_caseload_res = result
        else:
            # Handle the case where no resource was available (shouldn't happen as function keeps checking)
            print("No available resource found!")
            
        if g.debug_level >=2:
            print(f'Resource {self.cbt_caseload_id} with a caseload remaining of {self.cbt_caseload_res.level} allocated to patient {p.id}')
        
        with self.cbt_caseload_res.get(1) as self.cbt_req:
            yield self.cbt_req

        # # create a variable to store the current level of the caseload for this resource
        # self.pwp_caseload_posn = self.caseload_[f'{self.caseload_id}']
        # # add to this specific caseload
        # self.pwp_caseload_posn +=1

        if g.debug_level >=2:
            print(f'Patient {p.id} added to caseload {self.cbt_caseload_id}, {self.cbt_resources[self.cbt_caseload_id].level} spaces left')

        # add to overall caseload
        g.number_on_cbt_cl +=1

        # print(f'Patient {p} started CBT')

        # as each patient reaches this stage take them off CBT WL
        g.number_on_cbt_wl -= 1

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} removed from {p.step3_path_route} waiting list')

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step3_cbt_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) put through {p.step3_path_route}')

        end_q_cbt = self.env.now

        p.step3_start_week = self.week_number

        # Calculate how long patient queued for CBT
        self.q_time_cbt = end_q_cbt - start_q_cbt
        # Record how long patient queued for CBT
        self.asst_results_df.at[p.id, 'CBT Q Time'] = self.q_time_cbt

        # Generate a list of week numbers the patient is going to attend
        self.cbt_random_weeks = random.sample(range(self.week_number+1, self.week_number+g.step3_cbt_period), g.step3_cbt_sessions)

        # Add 1 at the start of the list
        self.cbt_random_weeks.insert(0, 0)

        # Optionally, sort the list to maintain sequential order
        self.cbt_random_weeks.sort()

        # print(self.random_weeks)

        while self.cbt_session_counter < g.step3_cbt_sessions and self.cbt_dna_counter < 2:

            if g.debug_level >= 2:
                print(f'FUNC PROCESS step3_cbt_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) on {p.step3_path_route} Session {self.cbt_session_counter} on Week {self.week_number + self.cbt_random_weeks[self.cbt_session_counter]}')

            # increment the pwp session counter by 1
            self.cbt_session_counter += 1

            # record the pwp session number for the patient
            self.step3_results_df.at[p.id, 'Session Number'] = self.cbt_session_counter

            
            # record stats for the patient against this session number
            self.step3_results_df.at[p.id,'Patient ID'] = p
            self.step3_results_df.at[p.id,'Week Number'] = self.week_number + self.cbt_random_weeks[self.cbt_session_counter]
            self.step3_results_df.at[p.id,'Run Number'] = self.run_number
            self.step3_results_df.at[p.id, 'Treatment Route'
                                                ] = p.step3_path_route
     
            # decide whether the patient was stepped down
            self.step_patient_down = random.uniform(0,1)
            # is the patient approaching the end of treatment and do they need to be stepped down?
            if self.cbt_session_counter >= g.step3_cbt_sessions-1 and self.step_patient_down <= g.step_down_rate:
                
                self.step3_results_df['IsStepDown'] = 1
                
                if g.debug_level >= 2:
                    print(f'### STEPPED DOWN ###: Patient {p.id} has been stepped down, running Step2 route selector')
                yield self.env.process(self.patient_step2_pathway(p))
            else:
                self.step2_results_df['IsStepDown'] = 0

                # decide whether the session was DNA'd
                self.dna_cbt_session = random.uniform(0,1)

                if self.dna_cbt_session <= g.step3_cbt_dna_rate:
                    self.step3_results_df.at[p.id, 'IsDNA'] = 1
                    self.cbt_dna_counter += 1
                    # if session is DNA just record admin mins as clinical time will be used elsewhere
                    self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin
                    if g.debug_level >= 2:
                        print(f'Patient number {p.id} on {p.step3_path_route}' 
                            f' Session {self.cbt_session_counter} DNA number ' 
                            f'{self.cbt_dna_counter}')
                else:
                    self.step3_results_df.at[p.id, 'IsDNA'] = 0
                    if self.cbt_session_counter == 1:
                        # if it's the 1st session use 1st session time
                        self.step3_results_df.at[p.id,'Session Time'] = g.step3_cbt_1st_mins
                        self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin
                    else:
                        # otherwise use follow-up session time
                        self.step3_results_df.at[p.id,'Session Time'] = g.step3_cbt_fup_mins
                        self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin

        # record whether patient dropped out before completing Wellbeing Workshop
        if self.cbt_dna_counter >= 2:
            self.step3_results_df.at[p.id, 'IsDropOut'] = 1
            if g.debug_level >= 2:
                print(f'Patient {p.id} dropped out of {p.step3_path_route} treatment')
            p.step3_end_week = p.step3_start_week+self.cbt_random_weeks[self.cbt_session_counter]
        else:
            self.step3_results_df.at[p.id, 'IsDropOut'] = 0
            if g.debug_level >= 2:
                print(f'Patient {p.id} completed {p.step3_path_route} treatment')
            p.step3_end_week = p.step3_start_week+max(self.cbt_random_weeks)

        # remove from Step 3 Caseload as have either completed treatment or dropped out
        self.step3_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for cbt sessions
        self.cbt_session_counter = 0
        self.cbt_dna_counter = 0

        # remove from overall caseload
        g.number_on_cbt_cl -=1

        # # remove from clinician caseload
        # self.cbt_caseloads[self.cbt_caseload_id] -=1

        # Return CBT caseload resource to the container
        with self.cbt_caseload_res.put(1) as cbt_rel:
            yield cbt_rel

        if self.cbt_dna_counter >= 2:
            # if patient dropped out hold onto the resource latest attended session
            yield self.env.timeout(self.cbt_random_weeks[self.cbt_session_counter])
            if g.debug_level >= 2:
                print(f'Patient {p.id} starting at week {p.step3_start_week} discharged from {p.step3_path_route} at week {p.step3_end_week}')
        else:
            # otherwise hold onto the resource until the last session
            yield self.env.timeout(max(self.cbt_random_weeks))
            if g.debug_level >= 2:
                print(f'Patient {p.id} starting at week {p.step3_start_week} discharged from {p.step3_path_route} at week {p.step3_end_week}')

        # remove this patient from the sim
        self.referral_tracker -= 1

    def step3_couns_process(self,patient):

        p = patient

        # counter for number of couns sessions
        self.couns_session_counter = 0
        # counter for applying DNA policy
        self.couns_dna_counter = 0

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} added to {p.step3_path_route} waiting list')

        start_q_couns = self.env.now

        # Record where the patient is on the TA WL
        self.step3_results_df.at[p.id, 'Couns WL Posn'] = \
                                            g.number_on_couns_wl

        # Check if there is a caseload slot available and return the resource
        result = yield self.env.process(self.find_caseload_slot('Couns'))

        # Safeguard unpacking: Ensure result is not None and has two elements
        if result:
            self.couns_caseload_id, self.couns_caseload_res = result
        else:
            # Handle the case where no resource was available (shouldn't happen as function keeps checking)
            print("No available resource found!")
            
        if g.debug_level >=2:
            print(f'Resource {self.couns_caseload_id} with a caseload remaining of {self.couns_caseload_res.level} allocated to patient {p.id}')
        
        with self.couns_caseload_res.get(1) as self.couns_req:
            yield self.couns_req

        # # create a variable to store the current level of the caseload for this resource
        # self.pwp_caseload_posn = self.caseload_[f'{self.caseload_id}']
        # # add to this specific caseload
        # self.pwp_caseload_posn +=1

        if g.debug_level >=2:
            print(f'Patient {p.id} added to caseload {self.couns_caseload_id}, {self.couns_resources[self.couns_caseload_id].level} spaces left')

        # add to overall caseload
        g.number_on_couns_cl +=1

        # print(f'Patient {p} started Couns')

        # as each patient reaches this stage take them off Couns WL
        g.number_on_couns_wl -= 1

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} removed from {p.step3_path_route} waiting list')

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step3_couns_process: Week {self.env.now}: Patient number {p.id} (added week {p.week_added}) put through {p.step3_path_route}')

        end_q_couns = self.env.now

        p.step3_start_week = self.week_number

        # Calculate how long patient queued for TA
        self.q_time_couns = end_q_couns - start_q_couns
        # Record how long patient queued for TA
        self.asst_results_df.at[p.id, 'Couns Q Time'] = self.q_time_couns

        # Generate a list of week numbers the patient is going to attend
        self.couns_random_weeks = random.sample(range(self.week_number+1, self.week_number+g.step3_couns_period), g.step3_couns_sessions)

        # always start at week 0
        self.couns_random_weeks.insert(0, 0)

        # sort the list to maintain sequential order
        self.couns_random_weeks.sort()

        # print(self.counsrandom_weeks)

        while self.couns_session_counter < g.step3_couns_sessions and self.couns_dna_counter < 2:

            if g.debug_level >= 2:
                print(f'FUNC PROCESS step3_cbt_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) on {p.step3_path_route} Session {self.couns_session_counter} on Week {self.week_number + self.couns_random_weeks[self.couns_session_counter]}')

            # increment the pwp session counter by 1
            self.couns_session_counter += 1

            # record the pwp session number for the patient
            self.step3_results_df.at[p.id, 'Session Number'] = self.couns_session_counter

            
            # record stats for the patient against this session number
            self.step3_results_df.at[p.id,'Patient ID'] = p
            self.step3_results_df.at[p.id,'Week Number'] = self.week_number + self.couns_random_weeks[self.couns_session_counter]
            self.step3_results_df.at[p.id,'Run Number'] = self.run_number
            self.step3_results_df.at[p.id, 'Treatment Route'
                                                ] = p.step3_path_route
 
            # decide whether the patient was stepped down
            self.step_patient_down = random.uniform(0,1)
            # is the patient approaching the end of treatment and do they need to be stepped down?
            if self.couns_session_counter >= g.step3_couns_sessions-2 and self.step_patient_down <= g.step_down_rate:
                
                self.step3_results_df['IsStepDown'] = 1
                
                if g.debug_level >= 2:
                    print(f'### STEPPED DOWN ###: Patient {p.id} has been stepped down, running Step2 route selector')
                self.step3_results_df.at[p.id, 'IsDropOut'] = 0
                if g.debug_level >= 2:
                    print(f'Patient {p.id} completed {p.step3_path_route} treatment')
                # remove from Step 2 Caseload as have either completed treatment or dropped out
                self.step3_results_df.at[p.id, 'Caseload'] = 0

                # reset counters for couns sessions
                self.couns_session_counter = 0
                self.couns_dna_counter = 0

                # add to caseload
                g.number_on_couns_cl -=1
                
                yield self.env.process(self.patient_step2_pathway(p))
            else:
                self.step2_results_df['IsStepDown'] = 0

                # decide whether the session was DNA'd
                self.dna_couns_session = random.uniform(0,1)

                if self.dna_couns_session <= g.step3_couns_dna_rate:
                    self.step3_results_df.at[p.id, 'IsDNA'] = 1
                    self.couns_dna_counter += 1
                    # if session is DNA just record admin mins as clinical time will be used elsewhere
                    self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin
                    if g.debug_level >= 2:
                        print(f'Patient {p.id} on {p.step3_path_route} Session'
                            f'{self.couns_session_counter} DNA number' 
                            f'{self.couns_dna_counter}')
                else:
                    self.step3_results_df.at[p.id, 'IsDNA'] = 0
                    if self.couns_session_counter == 1:
                        # if it's the 1st session use 1st session time
                        self.step3_results_df.at[p.id,'Session Time'] = g.step3_couns_1st_mins
                        self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin
                    else:
                        # otherwise use follow-up session time
                        self.step3_results_df.at[p.id,'Session Time'] = g.step3_couns_fup_mins
                        self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin

        # record whether patient dropped out before completing Wellbeing Workshop
        if self.couns_dna_counter >= 2:
            self.step3_results_df.at[p.id, 'IsDropOut'] = 1
            if g.debug_level >= 2:
                print(f'Patient {p.id} dropped out of {p.step3_path_route} treatment')
            p.step3_end_week = p.step3_start_week+self.couns_random_weeks[self.couns_session_counter]
        else:
            self.step3_results_df.at[p.id, 'IsDropOut'] = 0
            if g.debug_level >= 2:
                print(f'Patient {p.id} completed {p.step3_path_route} treatment')
            p.step3_end_week = p.step3_start_week+max(self.couns_random_weeks)
        # remove from Step 3 Caseload as have either completed treatment or dropped out
        self.step3_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for couns sessions
        self.couns_session_counter = 0
        self.couns_dna_counter = 0

        # remove from overall caseload
        g.number_on_couns_cl -=1

        # # remove from clinician caseload
        # self.couns_caseloads[self.couns_caseload_id] -=1

        # remove from caseload
        g.number_on_couns_cl -=1

        # Return Couns caseload resource to the container
        with self.couns_caseload_res.put(1) as couns_rel:
            yield couns_rel
        
        if self.couns_dna_counter >= 2:
            # if patient dropped out hold onto the resource latest attended session
            yield self.env.timeout(self.couns_random_weeks[self.couns_session_counter])
            if g.debug_level >= 2:
                print(f'Patient {p.id} starting at week {p.step3_start_week} discharged from {p.step3_path_route} at week {p.step3_end_week}')
        else:
            # otherwise hold onto the resource until the last session
            yield self.env.timeout(max(self.couns_random_weeks))
            if g.debug_level >= 2:
                print(f'Patient {p.id} starting at week {p.step3_start_week} discharged from {p.step3_path_route} at week {p.step3_end_week}')

        # remove this patient from the sim
        self.referral_tracker -= 1

    # This method calculates results over each single run
    def calculate_run_results(self):
        # Take the mean of the queuing times etc.
        self.mean_screen_time = self.asst_results_df['Referral Time Screen'].mean()
        self.reject_ref_total = self.asst_results_df['Referral Rejected'].sum()
        self.mean_optin_wait = self.asst_results_df['Opt-in Wait'].mean()
        self.ref_tot_optin = self.asst_results_df['Opted In'].sum()
        self.mean_qtime_ta =  self.asst_results_df['Opt-in Q Time'].mean()
        self.tot_ta_accept = self.asst_results_df['TA Outcome'].sum()
        
        # reset waiting lists and caseloads ready for next run
        g.number_on_pwp_wl = 0
        g.number_on_group_wl = 0
        g.number_on_cbt_wl = 0
        g.number_on_couns_wl = 0
        g.number_on_pwp_cl = 0
        g.number_on_group_cl = 0
        g.number_on_cbt_cl = 0
        g.number_on_couns_cl = 0

    # The run method starts up the DES entity generators, runs the simulation,
    # and in turns calls anything we need to generate results for the run
    def run(self, print_run_results=True):

        self.referras_generated = [] # list to hold the weekly referrals generated
        self.referral_tracker = 0 # counter for referrals received and processed

        # create a simpy store for this run to hold the patients until the group 
        # has enough members. This will persist for an entire run has finished 
        # and patients will be added to it and taken out of it as groups fill up 
        # and are run
        self.group_store = simpy.Store(
                                        self.env,
                                        capacity=g.step2_group_size
                                        )

        # Start up the resource builder to set up all staff resources
        self.env.process(self.resource_builder())

        # Start up the week runner to process patients
        self.env.process(self.week_runner(g.sim_duration))

        # Run the model
        self.env.run()

        # Now the simulation run has finished, call the method that calculates
        # run results
        self.calculate_run_results()

        # Print the run number with the patient-level results from this run of
        # the model
        if print_run_results:
            #print(g.weekly_wl_posn)
            print (f"Run Number {self.run_number}")
            print (self.asst_results_df)

# Class representing a Trial for our simulation - a batch of simulation runs.
class Trial:
    # The constructor sets up a pandas dataframe that will store the key
    # results from each run against run number, with run number as the index.
    def  __init__(self):
        self.df_trial_results = pd.DataFrame()
        self.df_trial_results["Run Number"] = [0]
        self.df_trial_results["Mean Screen Time"] = [0.0]
        self.df_trial_results["Total Referrals Rejected"] = [0]
        self.df_trial_results["Mean Opt-in Wait"] = [0.0]
        self.df_trial_results["Total Opted In"] = [0]
        self.df_trial_results["Mean Q Time TA"] = [0.0]
        self.df_trial_results["Total Accepted"] = [0]
        self.df_trial_results.set_index("Run Number", inplace=True)

        self.asst_weekly_dfs = []
        self.step2_weekly_dfs = []
        self.step3_weekly_dfs = []
        self.staff_weekly_dfs = []

    # Method to print out the results from the trial.  In real world models,
    # you'd likely save them as well as (or instead of) printing them
    def print_trial_results(self):
        print ("Trial Results")
        print (self.df_trial_results)

    # Method to run a trial
    def run_trial(self):
        # Run the simulation for the number of runs specified in g class.
        # For each run, we create a new instance of the Model class and call its
        # run method, which sets everything else in motion.  Once the run has
        # completed, we grab out the stored run results and store it against
        # the run number in the trial results dataframe
        for run in range(g.number_of_runs):
            my_model = Model(run)
            my_model.run(print_run_results=False)

            self.df_trial_results.loc[run] = [
                my_model.mean_screen_time,
                my_model.reject_ref_total,
                my_model.mean_optin_wait,
                my_model.ref_tot_optin,
                my_model.mean_qtime_ta,
                my_model.tot_ta_accept
                ]

            # turn weekly stats into a dataframe
            my_model.asst_weekly_stats = pd.DataFrame(my_model.asst_weekly_stats)
            my_model.step2_weekly_stats = pd.DataFrame(my_model.step2_weekly_stats)
            my_model.step3_weekly_stats = pd.DataFrame(my_model.step3_weekly_stats)
            my_model.staff_weekly_stats = pd.DataFrame(my_model.staff_weekly_stats)

            # add the run number to the dataframe
            my_model.asst_weekly_stats['Run'] = run
            my_model.step2_weekly_stats['Run'] = run
            my_model.step3_weekly_stats['Run'] = run
            my_model.staff_weekly_stats['Run'] = run

            #print(my_model.asst_weekly_stats)
            # append stats for that week to each combined dataframe
            self.asst_weekly_dfs.append(my_model.asst_weekly_stats)
            self.step2_weekly_dfs.append(my_model.step2_weekly_stats)
            self.step3_weekly_dfs.append(my_model.step3_weekly_stats)
            self.staff_weekly_dfs.append(my_model.staff_weekly_stats)

            self.caseload_weekly_dfs = pd.json_normalize(g.caseload_weekly_stats, 'Data', ['Run Number', 'Week Number'])


        # Once the trial (i.e. all runs) has completed, print the final results and combine all the weekly dataframes
        return self.df_trial_results, pd.concat(self.asst_weekly_dfs), pd.concat(self.step2_weekly_dfs), pd.concat(self.step3_weekly_dfs), pd.concat(self.staff_weekly_dfs), self.caseload_weekly_dfs

if __name__ == "__main__":
    my_trial = Trial()
    #pd.set_option('display.max_rows', 1000)
    # Call the run_trial method of our Trial class object

    df_trial_results, asst_weekly_dfs, step2_weekly_dfs, step3_weekly_dfs, staff_weekly_dfs, caseload_weekly_dfs  = my_trial.run_trial()

#df_trial_results, print(asst_weekly_dfs.to_string()), print(step2_weekly_dfs.to_string()), print(step3_weekly_dfs.to_string()), staff_weekly_dfs, print(caseload_weekly_dfs.to_string())

# asst_weekly_dfs.to_csv('S:\Departmental Shares\IM&T\Information\Business Intelligence\Heath McDonald\HSMA\Discrete Event Simulations\IAPT DES\asst_weekly_summary.csv')
# step2_weekly_dfs.to_csv('step2_weekly_summary.csv')
# step3_weekly_dfs.to_csv('step3_weekly_summary.csv')
# caseload_weekly_dfs.to_csv('caseload_weekly_summary.csv')

#S:\Departmental Shares\IM&T\Information\Business Intelligence\Heath McDonald\HSMA\Discrete Event Simulations\IAPT DES


