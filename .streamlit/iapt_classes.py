import simpy
import random
import numpy as np
import pandas as pd
import math

class g:

    # used for testing
    debug_level = 2

    # Referrals
    mean_referrals_pw = 200

    # Screening
    referral_rej_rate = 0.3 # % of referrals rejected, advised 30%
    referral_review_rate = 0.4 # % that go to MDT as prev contact with Trust
    mdt_freq = 2 # how often in weeks MDT takes place, longest time a review referral may wait for review
    review_rej_rate = 0.5 # % ref that go to MDT and get rejected
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
    step2_ratio = 0.47 # proportion of patients that go onto Step2 vs Step3
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
    step3_routes =['CBT','Couns'] # full pathway options = ['PfCBT','Group','CBT','EMDR','DepC','DIT','IPT','CDEP']
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
    step_3_session_var = 0.15 # % of instances where number sessions goes over standard amount

    # Staff
    supervision_time = 120 # 2 hours per month per modality ##### could use modulus for every 4th week
    break_time = 100 # 20 mins per day
    wellbeing_time = 120 # 2 hours allocated per month
    counsellors_huddle = 30 # 30 mins p/w or 1 hr per fortnight
    cpd_time = 225 # half day per month CPD
    
    # Job Plans
    number_staff_cbt = 14 #138
    number_staff_couns = 4 #40
    number_staff_pwp = 12 #125
    hours_avail_cbt = 22.0
    hours_avail_couns = 22.0
    hours_avail_pwp = 21.0
    ta_resource = number_staff_pwp * 3 # job plan = 3 TA per week per PwP
    pwp_caseload = 20
    group_resource = number_staff_pwp #  job plan = 1 group per week per PwP, assume 12 per group
    cbt_caseload = 5
    couns_caseload = 5
    dna_policy = 2 # number of DNA's allowed before discharged
    dna_policy_var = 0.05 # % of cases where the DNA policy is varied

    # Simulation
    sim_duration = 52
    number_of_runs = 5
    std_dev = 3 # used for randomising activity times
    #event_week_tracker = {} # used to track the latest events week for each patient

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
# function to vary the number of sessions
def vary_number_sessions(lower, upper, lambda_val=0.1):
        
        while True:
            # Generate a random number from the exponential distribution
            random_value = np.random.exponential(1 / lambda_val)

            # Shift the distribution to start at 'lower'
            sessions = random_value + lower #added lower to the random value.

            # Check if the generated value is within the desired range
            if lower <= sessions <= upper:
                # Convert to integer and return
                return int(sessions)

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
        self.referral_review_rej = 0
        self.time_to_mdt = 0 # how long to MDT, max 2 weeks
        self.opted_in = 0 # did the patient opt in or not
        self.opt_in_wait = 0 # how much of 1 week opt-in window was used
        self.opt_in_qtime = 0 # how much of 4 week TA app window was used
        self.attended_ta = 0 # did the patient attend TA appointment
        self.treat_wait_week = 0 # week they started waiting to enter treatment

        self.initial_step = [] # string, whether they were step 2 or step 3

        # Step2
        self.step2_resource_id = [] # identifier for the staff member allocated to their treatment
        self.step2_path_route = [] # string, which Step2 path they took
        self.step2_place_on_wl = 0 # position they are on Step2 waiting list
        self.step2_wait_week = 0 # week they started waiting to enter treatment
        self.step2_start_week = 0 # the week number they started treatment
        self.step2_session_count = 0 # counter for no. of sessions have had
        self.step2_drop_out = 0 # did they drop out during Step2
        self.step2_week_number = 0 # counter for which week number they are on
        self.step2_end_week = 0 # the week number when they completed treatment

        # Step3
        self.step3_resource_id = [] # identifier for the staff member allocated to their treatment
        self.step3_path_route = [] # string, which Step2 path they took
        self.step3_place_on_wl = 0 # position they are on Step2 waiting list
        self.step2_wait_week = 0 # week they started waiting to enter treatment
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
        self.asst_results_df['Referral Accepted'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Referral Reviewed'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Review Wait'] = [0] # time between screening and getting review
        self.asst_results_df['Review Rejected'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Opted In'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Opt-in Wait'] = [0.0] # time between opt-in notification and patient opting in
        self.asst_results_df['Opt-in Q Time'] = [0.0] # time between opting in and actual TA, 4 week window
        self.asst_results_df['TA Q Time'] = [0] # time spent queueing for TA
        self.asst_results_df['TA WL Posn'] = [0] # position in queue for TA
        self.asst_results_df['TA Outcome'] = [0] # 1 = Accepted, 0 = Rejected
        self.asst_results_df['TA Mins'] = [0] # time allocated to completing TA
        self.asst_results_df['Treatment Path'] = ['NA']

        # Indexing
        self.asst_results_df.set_index("Patient ID", inplace=True)

        self.step2_waiting_list = pd.DataFrame()
        self.step2_waiting_list['Patient ID'] = [1]
        self.step2_waiting_list['Run Number'] = 0
        self.step2_waiting_list['Week Number'] = 0
        self.step2_waiting_list['Route Name'] = ['NA']
        self.step2_waiting_list['IsWaiting'] = 1
        self.step2_waiting_list['WL Position'] = 0
        self.step2_waiting_list['Start Week'] = 0
        self.step2_waiting_list['End Week'] = -1
        self.step2_waiting_list['Wait Time'] = 0.0

        self.step2_waiting_list.set_index("Patient ID", inplace=True)

        # Step2
        # Create a new DataFrame that will store opt-in results against the patient ID
        self.step2_results_df = pd.DataFrame()

        self.step2_sessions_df = pd.DataFrame()

        self.step2_results_df['Patient ID'] = [1]
        self.step2_results_df['Week Number'] = [0]
        self.step2_results_df['Run Number'] = [0]
        self.step2_results_df['Route Name'] = ['NA'] # which Step2 pathway the patient was sent down
        self.step2_results_df['Q Time'] = [0.0] # time spent queueing
        self.step2_results_df['WL Posn'] = [0] # place in queue 
        self.step2_results_df['IsDropout'] = [0]
        self.step2_results_df['IsStep'] = [0] # was the patent stepped down

        self.step2_sessions_df['Patient ID'] = [1]
        self.step2_sessions_df['Week Number'] = [0]
        self.step2_sessions_df['Run Number'] = [0]
        self.step2_sessions_df['Route Name'] = ['NA'] # which Step2 pathway the patient was sent down
        self.step2_sessions_df['Session Number'] = [0]
        self.step2_sessions_df['Session Time'] = [0] # clinical session time in mins
        self.step2_sessions_df['Admin Time'] = [0] # admin session time in mins
        self.step2_sessions_df['IsDNA'] = [0]
       
        # Indexing
        self.step2_results_df.set_index("Patient ID", inplace=True)
        self.step2_sessions_df.set_index("Patient ID", inplace=True)

        # Step3
        # Create DataFrames that will store Step3 results against the patient ID
        
        self.step3_waiting_list = pd.DataFrame()
        self.step3_waiting_list['Patient ID'] = [1]
        self.step3_waiting_list['Run Number'] = 0
        self.step3_waiting_list['Week Number'] = 0
        self.step3_waiting_list['Route Name'] = ['NA']
        self.step3_waiting_list['IsWaiting'] = 1
        self.step3_waiting_list['WL Position'] = 0
        self.step3_waiting_list['Start Week'] = 0
        self.step3_waiting_list['End Week'] = -1
        self.step3_waiting_list['Wait Time'] = 0.0

        self.step3_waiting_list.set_index("Patient ID", inplace=True)

        self.step3_results_df = pd.DataFrame()
        self.step3_sessions_df = pd.DataFrame()

        self.step3_results_df['Patient ID'] = [1]
        self.step3_results_df['Week Number'] = [0]
        self.step3_results_df['Run Number'] = [0]
        self.step3_results_df['Route Name'] = ['NA'] # which Step3 pathway the patient was sent down
        self.step3_results_df['WL Posn'] = [0] # place in queue
        self.step3_results_df['Q Time'] = [0.0] # time spent queueing 
        self.step3_results_df['IsDropout'] = [0]
        self.step3_results_df['IsStep'] = [0] # was the patent stepped down

        self.step3_sessions_df['Patient ID'] = [1]
        self.step3_sessions_df['Week Number'] = [0]
        self.step3_sessions_df['Run Number'] = [0]
        self.step3_sessions_df['Route Name'] = ['NA'] # which Step2 pathway the patient was sent down
        self.step3_sessions_df['Session Number'] = [0]
        self.step3_sessions_df['Session Time'] = [0] # clinical session time in mins
        self.step3_sessions_df['Admin Time'] = [0] # admin session time in mins
        self.step3_sessions_df['IsDNA'] = [0]

        # Indexing
        self.step3_results_df.set_index("Patient ID", inplace=True)
        self.step3_sessions_df.set_index("Patient ID", inplace=True)

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
           
    # master process to control the running of all the other processes
    def the_governor(self):

        # start off the governor at week 0
        self.week_number = 0

        # build the caseload resources here, these will be topped up periodically
        yield self.env.process(self.caseload_builder())

        if g.debug_level >= 2:
                    print(f"Building Sim Resources")
                   
        # build the weekly resources needed to run the model
        yield self.env.process(self.resource_builder())

        if g.debug_level >= 2:
                    print(f"Sim Resources Ready")


        if g.debug_level >= 2:
                    print(f"Caseload Resources Ready")

        # list to hold weekly asst statistics
        self.asst_weekly_stats = []
        # list to hold weekly Step2 statistics
        self.step2_weekly_stats = []
        # list to hold weekly Step3 statistics
        self.step3_weekly_stats = []
        # list to hold weekly Staff statistics
        self.staff_weekly_stats = []
        # list to hold Step2 waiting list
        self.step2_waiting_stats = []
        # list to hold Step3 waiting list
        self.step3_waiting_stats = []

        # run for however many times there are weeks in the sim
        while self.week_number < g.sim_duration:

            if g.debug_level >= 2:

                print(f'''
                #################################
                        Week Number {self.week_number} 
                #################################
                ''')

            if g.debug_level >= 2:
                    print(f"Topping Up Resources")
            # top up the weekly resources ready for next run
            yield self.env.process(self.replenish_weekly_resources())

            if g.debug_level >= 2:
                    print(f"Topping Up Caseloads")
            
            # top up the caseload resources ready for next run
            yield self.env.process(self.top_up_caseloads(self.week_number))
            
            if g.debug_level >= 2:
                    print(f"Firing up the staff entity generator")
            
            # start up the staff entity generator
            yield self.env.process(self.staff_entity_generator(self.week_number))

            if g.debug_level >= 2:
                    print(f"Staff generator complete")

            if g.debug_level >= 2:
                    print(f"Firing up the referral generator")
            # start up the referral generator
            yield self.env.process(self.generator_patient_referrals(self.week_number))
            
            if g.debug_level >= 2:
                    print(f"Referral generator has returned {self.referrals_this_week} referrals")

            if g.debug_level >= 2:
                    print(f"Passing {self.referrals_this_week} to the patient treatment generator")

            # start up the patient treatment generator
            yield self.env.process(self.patient_treatment_generator(self.referrals_this_week,self.week_number))

            if g.debug_level >= 2:
                    print(f"Collecting Weekly Stats")
            
            # collect the weekly stats ready for the next week to run
            yield self.env.process(self.weekly_stats(self.week_number))

            if g.debug_level >= 2:
                    print(f"Weekly Stats have been collected")

        
            # increment the week number by one now everything has been run for this week
            self.week_number += 1

            if g.debug_level >= 2 and self.week_number<g.sim_duration:
                    print(f"Week {self.week_number-1} complete, moving on to Week {self.week_number}")
            elif g.debug_level >= 2 and self.week_number == g.sim_duration-1:
                print(f"Week {self.week_number-1} complete, simulation has now finished")

            # wait a week before moving onto the next week
            yield self.env.timeout(1)

    def patient_treatment_generator(self,number_of_referrals,treatment_week_number):

        self.referrals_to_process = number_of_referrals
        if g.debug_level >=2:
                print(f'Processing {number_of_referrals} referral through treatment')
        self.treatment_week_number = treatment_week_number

        while self.referrals_to_process > 0:

            if g.debug_level >=2:
                print(f'Processing referral, {self.referrals_to_process} left out of {number_of_referrals}')
            yield self.env.timeout(0) 
            self.env.process(self.screen_referral(self.treatment_week_number))
            
            self.referrals_to_process -= 1
            
            if g.debug_level >=2:
                print(f'Referral processed, proceeding to next referral, {self.referrals_to_process} left')

        # wait 1 unit of time i.e. 1 week
        #yield self.env.timeout(1)       

    # process to capture all the results we need at the end of each week
    def weekly_stats(self,stats_week_number):
          
            self.stats_week_number = stats_week_number

            self.asst_results_weekly_stats = self.asst_results_df[self.asst_results_df['Week Number'] == self.stats_week_number].copy()

            ##### record all weekly results #####
            ## Screening & TA
            self.referrals_recvd = self.referrals_this_week
            self.asst_tot_screen = self.asst_results_weekly_stats['Referral Time Screen'].sum()
            self.asst_tot_accept = self.asst_results_weekly_stats['Referral Accepted'].sum()
            self.asst_tot_reject = self.asst_results_weekly_stats['Referral Rejected'].sum()
            self.asst_tot_revwd = self.asst_results_weekly_stats['Referral Reviewed'].sum()
            self.asst_revw_reject = self.asst_results_weekly_stats['Review Rejected'].sum()
            self.asst_optin_delay = self.asst_results_weekly_stats['Opt-in Wait'].mean()
            self.asst_tot_optin = self.asst_results_weekly_stats['Opted In'].sum()
            self.asst_optin_wait = self.asst_results_weekly_stats['Opt-in Q Time'].mean()
            self.asst_waiting_list = g.number_on_ta_wl
            self.asst_avg_wait = self.asst_results_df['TA Q Time'].mean()
            self.asst_tot_accept = self.asst_results_df['TA Outcome'].sum()
            self.asst_time_total = self.asst_results_weekly_stats['TA Mins'].sum()

            self.asst_weekly_stats.append(
                {'Run Number': self.run_number,
                 'Week Number':self.stats_week_number,
                 'Referrals Received':self.referrals_recvd,
                 'Referral Screen Mins':self.asst_tot_screen,
                 'Referrals Accepted':self.asst_tot_accept,
                 'Referrals Rejected':self.asst_tot_reject,
                 'Referrals Reviewed':self.asst_tot_revwd,
                 'Reviews Rejected':self.asst_revw_reject,
                 'Referrals Delay Opt-in':self.asst_optin_delay,
                 'Referrals Opted-in':self.asst_tot_optin,
                 'Referrals Wait Opt-in':self.asst_optin_wait,
                 'TA Waiting List':self.asst_waiting_list,
                 'TA Avg Wait':self.asst_avg_wait,
                 'TA Total Accept':self.asst_tot_accept,
                 'TA Mins':self.asst_time_total
                }
                )
    
            ## Staff
            self.job_role_list = ['PwP','CBT','Couns']
            # create summary stats for each of the job roles
            for i, job_role in enumerate(self.job_role_list):
                # filter data for appropriate role
                self.staff_results_df_filtered = self.staff_results_df[
                (self.staff_results_df["Job Role"] == job_role) & 
                (self.staff_results_df["Week Number"] == self.stats_week_number)
                ]

            
                self.job_role_name = job_role
                
                self.staff_tot_superv = self.staff_results_df_filtered['Supervision Mins'].sum()
                self.staff_tot_break = self.staff_results_df_filtered['Break Mins'].sum()
                self.staff_tot_wellb = self.staff_results_df_filtered['Wellbeing Mins'].sum()
                self.staff_tot_huddle = self.staff_results_df_filtered['Huddle Mins'].sum()
                self.staff_tot_cpd = self.staff_results_df_filtered['CPD Mins'].sum()
 
                # weekly staff non-clinical activity
                self.staff_weekly_stats.append(
                    {'Run Number':self.run_number,
                    'Job Role':self.job_role_name,
                    'Week Number':self.stats_week_number,
                    'Supervision Mins':self.staff_tot_superv,
                    'Break Mins':self.staff_tot_break,
                    'Wellbeing Mins':self.staff_tot_wellb,
                    'Huddle Mins':self.staff_tot_huddle,
                    'CPD Mins':self.staff_tot_cpd
                    }
                    )
                
            ##### Take a snapshot of the weekly caseload levels #####
            
            self.weekly_pwp_snapshot = {'Run Number':self.run_number
                                       ,'Week Number':self.stats_week_number
                                       ,'Data':[]}
            
            for pwp_caseload_id, pwp_level in self.pwp_resources.items():
                self.weekly_pwp_snapshot['Data'].append({
                                            'Caseload ID':pwp_caseload_id
                                            ,'Caseload Level':pwp_level.level})
            
            g.caseload_weekly_stats.append(self.weekly_pwp_snapshot)
                
            self.weekly_cbt_snapshot = {'Run Number':self.run_number
                                       ,'Week Number':self.stats_week_number
                                       ,'Data':[]}
            
            for cbt_caseload_id, cbt_level in self.cbt_resources.items():
                self.weekly_cbt_snapshot['Data'].append({
                                            'Caseload ID':cbt_caseload_id
                                            ,'Caseload Level':cbt_level.level})
            
            g.caseload_weekly_stats.append(self.weekly_cbt_snapshot)
            
            self.weekly_couns_snapshot = {'Run Number':self.run_number
                                       ,'Week Number':self.stats_week_number
                                       ,'Data':[]}
            
            for couns_caseload_id, couns_level in self.couns_resources.items():
                self.weekly_couns_snapshot['Data'].append({
                                            'Caseload ID':couns_caseload_id
                                            ,'Caseload Level':couns_level.level})
                
            g.caseload_weekly_stats.append(self.weekly_couns_snapshot)

            # record weekly waiting list stats
            ##### Step 2 #####
            self.step2_weekly_waiting_stats = self.step2_waiting_list[self.step2_waiting_list['IsWaiting'] == 1].copy()
            self.step2_weekly_waiting_stats['Weeks Waited'] = self.stats_week_number - self.step2_weekly_waiting_stats['Start Week']
            
            self.waiting_list_path = ['PwP','Group']
            # create summary stats for each of the routes
            for y, pathway in enumerate(self.waiting_list_path):

                self.step2_weekly_waiting_filtered = self.step2_weekly_waiting_stats[self.step2_weekly_waiting_stats['Route Name'] == pathway]

                self.step2_waiting_count = self.step2_weekly_waiting_filtered['IsWaiting'].sum()
                self.step2_waiting_time = self.step2_weekly_waiting_filtered['Weeks Waited'].mean()

                if pd.isna(self.step2_waiting_time):
                    self.step2_waiting_time = 0
                
                self.step2_waiting_stats.append(
                    {'Run Number': self.run_number,
                    'Week Number':self.stats_week_number,
                    'Route Name':pathway,
                    'Num Waiting':self.step2_waiting_count,
                    'Avg Wait':self.step2_waiting_time
                    }
                    )
                # if g.debug_level == 1:
                #     print(self.step2_waiting_list)
                ##### Step 3 ##### 
                # record weekly waiting list stats
            self.step3_weekly_waiting_stats = self.step3_waiting_list[self.step3_waiting_list['IsWaiting'] == 1].copy()
            self.step3_weekly_waiting_stats['Weeks Waited'] = self.stats_week_number - self.step3_weekly_waiting_stats['Start Week']
            
            self.waiting_list_path = ['Couns','CBT']
            # create summary stats for each of the routes
            for z, pathway in enumerate(self.waiting_list_path):

                self.step3_weekly_waiting_filtered = self.step3_weekly_waiting_stats[self.step3_weekly_waiting_stats['Route Name'] == pathway]

                self.step3_waiting_count = self.step3_weekly_waiting_filtered['IsWaiting'].sum()
                self.step3_waiting_time = self.step3_weekly_waiting_filtered['Weeks Waited'].mean()

                if pd.isna(self.step3_waiting_time):
                    self.step3_waiting_time = 0
                
                self.step3_waiting_stats.append(
                    {'Run Number': self.run_number,
                    'Week Number':self.stats_week_number,
                    'Route Name':pathway,
                    'Num Waiting':self.step3_waiting_count,
                    'Avg Wait':self.step3_waiting_time
                    }
                    )
                if g.debug_level == 1:
                    print(self.step3_waiting_list)
            # hand control back to the governor function
            yield self.env.timeout(0)

    ##### generator function that represents the DES generator for referrals
    def generator_patient_referrals(self,ref_week_number):

        #while ref_week_number < g.sim_duration:
        self.ref_week_number = ref_week_number

        # get the number of referrals that week based on the mean + seasonal variance
        self.referrals_this_week = round(g.mean_referrals_pw +
                                    (g.mean_referrals_pw *
                                    g.referral_rate_lookup.at[
                                    self.ref_week_number+1,'PCVar'])) # weeks start at 1

        if g.debug_level >= 1:
            print(f'Week {self.week_number}: {self.referrals_this_week}'
                                                    ' referrals generated')
        
        yield self.env.timeout(0)   
    
    # this function builds staff resources containing the number of slots on the caseload
    # or the number of weekly appointment slots available
    def resource_builder(self):

        ########## Weekly Resources ##########
        ##### TA #####
        self.ta_res = simpy.Container(
            self.env,capacity=g.ta_resource,
            init=g.ta_resource
            )
        ##### Group #####
        self.group_res = simpy.Container(
            self.env,
            capacity=g.group_resource,
            init=g.group_resource
            )
        
        yield(self.env.timeout(0))

    def caseload_builder(self):

        ##### PwP #####
        self.p_type = 'PwP'
        # dictionary to hold PwP caseload resources
        self.pwp_resources = {f'{self.p_type}_{p}':simpy.Container(self.env,
                    capacity=g.pwp_caseload,
                    init=g.pwp_caseload) for p in range(g.number_staff_pwp)}

        self.weekly_usage = {week: {"week_number": 0, "res_topup": 0} for week in range(g.sim_duration)}

        # dictionary to keep track of resources to be restored
        self.pwp_restore = {f'{self.p_type}_{p}':{} for p in range(g.number_staff_pwp)}
        
        if g.debug_level >= 2:
            print(self.pwp_restore)
        ##### CBT #####
        self.c_type = 'CBT'
        # dictionary to hold CBT caseload resources
        self.cbt_resources = {f'{self.c_type}_{c}':simpy.Container(self.env,
                    capacity=g.cbt_caseload,
                    init=g.cbt_caseload) for c in range(g.number_staff_cbt)}
        
        # dictionary to keep track of resources to be restored
        self.cbt_restore = {f'{self.c_type}_{c}':{} for c in range(g.number_staff_cbt)}
        
        if g.debug_level >= 2:
            print(self.cbt_restore)
        ##### Couns #####
        self.s_type = 'Couns'
        # dictionary to hold Couns caseload resources
        self.couns_resources = {f'{self.s_type}_{s}':simpy.Container(self.env,
                    capacity=g.couns_caseload,
                    init=g.couns_caseload) for s in range(g.number_staff_couns)}

        # dictionary to keep track of resources to be restored
        self.couns_restore = {f'{self.s_type}_{s}':{} for s in range(g.number_staff_couns)}

        if g.debug_level >= 2:
            print(self.couns_restore)
        
        yield self.env.timeout(0)

    def record_caseload_use(self,r_type,r_id,week_number):
        
        self.restore_week = week_number
        
        # Load in the correct resource use dictionary
        if r_type == 'PwP':
            self.resources_used = self.pwp_restore
        elif r_type == 'CBT':
            self.resources_used = self.cbt_restore
        elif r_type == 'Couns':
            self.resources_used = self.couns_restore
        
        # if g.debug_level >= 2:
        #     print(f'resource used level was:{self.resources_used[r_id]}')
        
        if r_id not in self.resources_used:
            
            if g.debug_level >= 2:
                print(f"Error: {r_id} not found in {r_type} resources.")
            return

        # Ensure the week entry exists
        if self.restore_week not in self.resources_used[r_id]:
            self.resources_used[r_id][self.restore_week] = {"week_number": self.restore_week, "res_topup": 0}

        # Now safely update
        self.resources_used[r_id][self.restore_week]['res_topup'] += 1

        if g.debug_level >= 2:
            print(f"Resource {r_id} usage recorded for week {self.restore_week}: {self.resources_used[r_id][self.restore_week]}")

        yield self.env.timeout(0)

    def replenish_weekly_resources(self):

            ##### TA and Group Resources #####
            ta_amount_to_fill = g.ta_resource - self.ta_res.level
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

            # don't wait, go to the next step
            yield self.env.timeout(0)

    def top_up_caseloads(self,week_number):
            
             ##### Caseload Resources #####
            self.week_num = week_number

            for self.pwp_restore_id, week_data in self.pwp_restore.items():
                if self.week_num in week_data and week_data[self.week_num]['res_topup'] > 0:
                    self.pwp_topup_value = week_data[self.week_num]['res_topup']
                    if g.debug_level >= 2:
                        print(f"PwP Resource {self.pwp_restore_id} at week {self.week_num}: {self.pwp_resources[self.pwp_restore_id].level}, {self.pwp_topup_value} available to restore")

                    self.pwp_resources[self.pwp_restore_id].put(self.pwp_topup_value)

                if g.debug_level >= 2:
                    print(f"PwP Resource {self.pwp_restore_id} now at: {self.pwp_resources[self.pwp_restore_id].level}")
        
            for self.cbt_restore_id, week_data in self.cbt_restore.items():
                if self.week_num in week_data and week_data[self.week_num]['res_topup'] > 0:
                    self.cbt_topup_value = week_data[self.week_num]['res_topup']
                    if g.debug_level >= 2:
                        print(f"CBT Resource {self.cbt_restore_id} at week {self.week_num}: {self.cbt_resources[self.cbt_restore_id].level}, {self.cbt_topup_value} available to restore")

                    self.cbt_resources[self.cbt_restore_id].put(self.cbt_topup_value)

                if g.debug_level >= 2:
                    print(f"Couns Resource {self.cbt_restore_id} now at: {self.cbt_resources[self.cbt_restore_id].level}")
                      
            for self.couns_restore_id, week_data in self.couns_restore.items():
                if self.week_num in week_data and week_data[self.week_num]['res_topup'] > 0:
                    self.couns_topup_value = week_data[self.week_num]['res_topup']
                    if g.debug_level >= 2:
                            print(f"PwP Resource {self.couns_restore_id} at week {self.week_num}: {self.couns_resources[self.couns_restore_id].level}, {self.couns_topup_value} available to restore")

                    self.couns_resources[self.couns_restore_id].put(self.couns_topup_value)

                if g.debug_level >= 2:
                    print(f"PwP Resource {self.couns_restore_id} now at: {self.couns_resources[self.couns_restore_id].level}")
            # don't wait, go to the next step
            yield self.env.timeout(0)
            
    def find_caseload_slot(self,r_type):

        self.r_type = r_type
        # load in the right resource dictionary
        if self.r_type == 'PwP':
            self.resources = self.pwp_resources
        elif self.r_type == 'CBT':
            self.resources = self.cbt_resources
        elif self.r_type == 'Couns':
            self.resources = self.couns_resources

        self.available_caseloads = {k: v for k, v in self.resources.items() if v.level > 0}

        # keep going as long as the simulation is still running
        while self.env.now < g.sim_duration:
            if self.available_caseloads:
                # Randomly select from the non-empty resources
                self.random_caseload_id = random.choice(list(self.available_caseloads.keys()))
                self.selected_resource = self.available_caseloads[self.random_caseload_id]

                if g.debug_level >= 2:
                    print(f'Resource {self.random_caseload_id} with a remaining caseload of {self.selected_resource.level} selected')
                return self.random_caseload_id, self.selected_resource # Return the ID and the container if available
                yield self.env.timeout(0)
            else:
                if g.debug_level >=2:
                    print("No available caseload with spaces available!")
                return None, None
            
            yield self.env.timeout(1)
                     
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
    def screen_referral(self, asst_week_number):

        self.asst_week_number = asst_week_number

        # decide whether the referral was rejected at screening stage
        self.reject_referral = random.uniform(0,1)
                        
        # Increment the patient counter by 1
        self.patient_counter += 1

        # Create a new patient from Patient Class
        p = Patient(self.patient_counter)
        p.week_added = asst_week_number
        if g.debug_level >=2:
                print('')
                print(f"==== Patient {p.id} Generated ====")

        # all referrals get screened
        self.asst_results_df.at[p.id, 'Referral Time Screen'
                                        ] = self.random_normal(
                                        g.referral_screen_time
                                        ,g.std_dev)

        # check whether the referral was a straight reject or not
        if self.reject_referral > g.referral_rej_rate:

             # if this referral is accepted mark as accepted
            self.asst_results_df.at[p.id, 'Run Number'] = self.run_number

            self.asst_results_df.at[p.id, 'Week Number'] = self.asst_week_number

            self.asst_results_df.at[p.id, 'Referral Rejected'] = 0

            self.asst_results_df.at[p.id, 'Referral Accepted'] = 1

            if g.debug_level >=2:
                print(f"Referral Accepted flag set to {self.asst_results_df.at[p.id,'Referral Accepted']} for Patient {p.id}")
            # now review the patient
   
        else:

             # if this referral is rejected mark as rejected
            self.asst_results_df.at[p.id, 'Run Number'] = self.run_number

            self.asst_results_df.at[p.id, 'Week Number'] = self.asst_week_number

            self.asst_results_df.at[p.id, 'Referral Rejected'] = 1

            self.asst_results_df.at[p.id, 'Referral Accepted'] = 0

            if g.debug_level >=2:
                print(f"Referral Rejected for Patient {p.id}")

        if self.reject_referral > g.referral_rej_rate:
            yield self.env.process(self.review_referral(p))
        else:
            yield self.env.timeout(0)
  
    def review_referral(self,patient):

        # decide whether the referral needs to go for review if not rejected
        self.requires_review = random.uniform(0,1)
        # decide whether the referral is rejected at review
        self.review_reject = random.uniform(0,1)
        
        p = patient
        # patient needs to be reviewed
        if self.requires_review > g.referral_review_rate:

            if g.debug_level >=2:
                print(f"Patient {p.id} Sent For Review")
            # patient requires review and was rejected
            if self.review_reject < g.review_rej_rate:
                
                p.referral_review_rej = 1
                p.referral_req_review = 1
                
                self.asst_results_df.at[p.id,'Review Rejected'] = p.referral_review_rej
                
                if g.debug_level >=2:
                    print(f"Patient {p.id} Reviewed and Rejection flag set to {self.asst_results_df.at[p.id,'Review Rejected']}")

                # set flag to show Patient required review
                self.asst_results_df.at[p.id,'Referral Reviewed'] = p.referral_req_review
                # record how long they waited for MDT review between 0 and 2 weeks
                self.asst_results_df.at[p.id,'Review Wait'] = random.uniform(0,
                                                                g.mdt_freq)
                # set flag to show they were accepted and go to opt-in
                self.asst_results_df.at[p.id,'Review Rejected'] = p.referral_review_rej

                if g.debug_level >=2:
                    print(f"Patient {p.id} Rejected at Review")
                
            else:
                # patient requires review and was accepted
                p.referral_review_rej = 0
                p.referral_req_review = 1
                # set flag to show if Patient required review
                self.asst_results_df.at[p.id, 'Referral Reviewed'] = p.referral_req_review
                # therefore no review wait
                self.asst_results_df.at[p.id, 'Review Wait'] = random.uniform(0,
                                                            g.mdt_freq)
                # set flag to show they were accepted and go to opt-in
                self.asst_results_df.at[p.id, 'Review Rejected'] = p.referral_review_rej

                if g.debug_level >=2:
                    print(f"Patient {p.id} Reviewed and Rejection flag set to {self.asst_results_df.at[p.id,'Review Rejected']}")

                if g.debug_level >=2:
                    print(f"Patient {p.id} Accepted at Review - go to opt-in")
                             
        else:
            # patient didn't require review
            p.referral_review_rej = 0
            p.referral_req_review = 0
            if g.debug_level >=2:
                    print(f"Patient {p.id} Didn't Need Review")
            # patient didn't require reviews
            self.asst_results_df.at[p.id, 'Referral Reviewed'] = p.referral_req_review
            # therefore no review wait
            self.asst_results_df.at[p.id, 'Review Wait'] = 0
            # set flag to show they were accepted and go to opt-in
            self.asst_results_df.at[p.id, 'Review Rejected'] = p.referral_review_rej

            if g.debug_level >=2:
                print(f"Patient {p.id} Did Not Require Review, Rejection flag set to {self.asst_results_df.at[p.id,'Review Rejected']}")

            
            if g.debug_level >=2:
                print(f"Patient {p.id} did not require a Review - go to opt-in")

        if p.referral_review_rej == 1:
            yield self.env.timeout(0)
        else:
            # go to opt-in
            yield self.env.process(self.patient_opt_in(p))
    
    def patient_opt_in(self,patient):

        p = patient
        
        # now we can carry on and decide whether the patient opted-in or not
        self.patient_optedin = random.uniform(0,1)
        # decide whether the Patient is accepted following TA
        self.ta_accepted = random.uniform(0,1)
        
        if self.patient_optedin > g.opt_in_rate:
            # set flag to show Patient failed to opt-in
            self.asst_results_df.at[p.id, 'Opted In'] = 0
            if g.debug_level >=2:
                print(f"Patient {p.id} Failed to Opt In")
            # therefore didn't wait to opt-in
            self.asst_results_df.at[p.id, 'Opt-in Wait'] = 0
            # and didn't queue for TA appt
            self.asst_results_df.at[p.id, 'Opt-in Q Time'] = 0

            # # can stop here and move on to next patient
            yield self.env.timeout(0) 

        else: # self.patient_optedin < g.opt_in_rate:
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
            
            yield self.env.process(self.telephone_assessment(p))
            
    def telephone_assessment(self,patient):
            
            p = patient

            start_q_ta = self.env.now

            g.number_on_ta_wl += 1

            # Record where the patient is on the TA WL
            self.asst_results_df.at[p.id, "TA WL Posn"] = \
                                                g.number_on_ta_wl                                       

            # Request a Triage resource from the container
            if g.debug_level >=2:
                print(f"Patient {p.id} requesting TA resource, current res level {self.ta_res.level}")
            with self.ta_res.get(1) as ta_req:
                yield ta_req

            if g.debug_level >=2:
                print(f"Patient {p.id} allocated TA resource, new res level {self.ta_res.level}")

            # as each patient reaches this stage take them off TA wl
            g.number_on_ta_wl -= 1

            if g.debug_level >= 2:
                print(f'Week {self.env.now}: Patient number {p.id} (added week {p.week_added}) put through TA')

            end_q_ta = self.env.now

            # Calculate how long patient queued for TA
            self.q_time_ta = end_q_ta - start_q_ta
            # Record how long patient queued for TA
            self.asst_results_df.at[p.id, 'TA Q Time'] = self.q_time_ta

            if g.debug_level >=2:
                    print(f'Patient {p.id} waited {self.q_time_ta} for assessment')

            # Now do Telephone Assessment using mean and varying
            self.asst_results_df.at[p.id, 'TA Mins'
                                            ] = int(self.random_normal(
                                            g.ta_time_mins
                                            ,g.std_dev))
            
            # decide if the patient is accepted following TA
            if self.ta_accepted > g.ta_accept_rate:
                # Patient was rejected at TA stage
                self.asst_results_df.at[p.id, 'TA Outcome'] = 0
                if g.debug_level >=2:
                    print(f"Patient {p.id} Rejected at TA Stage")
                #yield self.env.timeout(0)

                # used to decide whether further parts of the pathway are run or not
                self.ta_accepted = 0
            else:
                # Patient was accepted at TA stage
                self.asst_results_df.at[p.id, 'TA Outcome'] = 1
                if g.debug_level >=2:
                    print(f"Patient {p.id} Accepted at TA Stage")

                # used to decide whether further parts of the pathway are run or not
                self.ta_accepted = 1

                # if patient was accepted decide which pathway the patient has been allocated to
                # Select 2 options based on the given probabilities
                self.step_options = random.choices(g.step_routes, weights=g.step2_step3_ratio, k=self.referrals_this_week)

                #print(self.selected_step)
                self.selected_step = random.choice(self.step_options)

                if self.selected_step == "Step3":
                    if g.debug_level >=2:
                        print(f"Selected step: **{self.selected_step}**")
                else:
                    if g.debug_level >=2:
                        print(f"Selected step: {self.selected_step}")

                self.asst_results_df.at[p.id, 'Treatment Path'] = self.selected_step
                p.initial_step = self.selected_step
                p.treat_wait_week = self.env.now # when they started waiting for treatment
                
                if g.debug_level >=2:
                    print(f"-- Pathway Runner Initiated --")
                
                # now run the pathway runner
                yield self.env.process(self.pathway_runner(p,p.initial_step))

    def pathway_runner(self, patient, step_chosen):

        p = patient

        if step_chosen == 'Step2':
            # record that they've started waiting for treatment
            #p.step2_wait_week = self.env.now
            
            if g.debug_level >=2:
                print(f'PATHWAY RUNNER: Patient {p.id} sent down **{p.initial_step}** pathway')
            #yield self.env.timeout(0)
            yield self.env.process(self.patient_step2_pathway(p))
        else:
            # record that they've started waiting for treatment
            #p.step3_wait_week = self.env.now
            if g.debug_level >=2:
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

        self.step2_results_df.at[p.id, 'Route Name'
                                            ] = p.step2_path_route

        # push the patient down the chosen step2 route
        if p.step2_path_route == 'PwP':
            # add to PwP WL
            g.number_on_pwp_wl += 1
            if g.debug_level >=2:
                print(f"Week Number {self.env.now}. Currently there are {g.number_on_pwp_wl} on the {p.step2_path_route} waiting list")
            # now we know which route they are taking, record waiting list data
            self.step2_waiting_list.at[p.id, 'Route Name'] = p.step2_path_route
            self.step2_waiting_list.at[p.id, 'Run Number'] = self.run_number
            self.step2_waiting_list.at[p.id, 'Week Number'] = self.week_number
            self.step2_waiting_list.at[p.id, 'IsWaiting'] = 1
            self.step2_waiting_list.at[p.id, 'WL Position'] = g.number_on_pwp_wl
            self.step2_waiting_list.at[p.id, 'Start Week'] = p.treat_wait_week

            #     self.step2_waiting_list['IsWaiting'] = 1
            # self.step2_waiting_list['WL Position'] = 0
            # self.step2_waiting_list['Start Week'] = 0

                        
            #yield self.env.timeout(0)
            yield self.env.process(self.step2_pwp_process(p))
        else:
            if g.debug_level >=2:
                print(f"Patient {p.id} sent to Group store")
            
                self.group_store.put(p)

                # add to group WL
                g.number_on_group_wl += 1

                if g.debug_level >=2:
                    print(f"Week Number {self.env.now}. Currently there are {g.number_on_pwp_wl} on the {p.step2_path_route} waiting list")
                
                if g.debug_level >=2:
                    print(f'Group store contains {len(self.group_store.items)} of possible {g.step2_group_size}')

                # self.start_q_group = self.env.now

                # now we know which route they are taking, record waiting list data
                self.step2_waiting_list.at[p.id, 'Route Name'] = p.step2_path_route
                self.step2_waiting_list.at[p.id, 'Run Number'] = self.run_number
                self.step2_waiting_list.at[p.id, 'Week Number'] = self.week_number
                self.step2_waiting_list.at[p.id, 'IsWaiting'] = 1
                self.step2_waiting_list.at[p.id, 'WL Position'] = g.number_on_group_wl
                self.step2_waiting_list.at[p.id, 'Start Week'] = p.treat_wait_week
                
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
                        #yield self.env.timeout(0)
                        yield self.env.process(self.step2_group_process(p))

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

        self.step3_results_df.at[p.id, 'Route Name'
                                            ] = p.step3_path_route

        # push the patient down the chosen step3 route
        if self.selected_step3_pathway == 'CBT':
            # add to CBT WL
            g.number_on_cbt_wl += 1

            if g.debug_level >=2:
                print(f"Week Number {self.env.now}. Currently there are {g.number_on_cbt_wl} on the {p.step3_path_route} waiting list")

            # now we know which route they are taking, record waiting list data
            self.step3_waiting_list.at[p.id, 'Route Name'] = self.selected_step3_pathway
            self.step3_waiting_list.at[p.id, 'Run Number'] = self.run_number
            self.step3_waiting_list.at[p.id, 'Week Number'] = self.week_number
            self.step3_waiting_list.at[p.id, 'IsWaiting'] = 1
            self.step3_waiting_list.at[p.id, 'WL Position'] = g.number_on_cbt_wl
            self.step3_waiting_list.at[p.id, 'Start Week'] = p.treat_wait_week
            
            if g.debug_level >=2:
                print(f"FUNC PROCESS patient_step3_pathway: Patient {p.id} Initiating {p.step3_path_route} Step 3 Route")
            #yield self.env.timeout(0)
            yield self.env.process(self.step3_cbt_process(p))
        else:
            # add to Couns WL
            g.number_on_couns_wl += 1

            if g.debug_level >=2:
                print(f"Week Number {self.env.now}. Currently there are {g.number_on_couns_wl} on the {p.step3_path_route} waiting list")

            # now we know which route they are taking, record waiting list data
            self.step3_waiting_list.at[p.id, 'Route Name'] = p.step3_path_route
            self.step3_waiting_list.at[p.id, 'Run Number'] = self.run_number
            self.step3_waiting_list.at[p.id, 'Week Number'] = self.week_number
            self.step3_waiting_list.at[p.id, 'IsWaiting'] = 1
            self.step3_waiting_list.at[p.id, 'WL Position'] = g.number_on_couns_wl
            self.step3_waiting_list.at[p.id, 'Start Week'] = p.treat_wait_week
            
            if g.debug_level >=2:
                print(f"FUNC PROCESS patient_step3_pathway: Patient {p.id} Initiating {p.step3_path_route} Step 3 Route")
            #yield self.env.timeout(0)
            yield self.env.process(self.step3_couns_process(p))
        #yield self.env.timeout(0)

    def step2_pwp_process(self,patient):

        p = patient

        # counter for number of group sessions
        self.pwp_session_counter = 0
        # counter for applying DNA policy
        self.pwp_dna_counter = 0

        if g.debug_level >=2:
            print(f'{p.step2_path_route} RUNNER: Patient {p.id} added to {p.step2_path_route} waiting list')

        self.start_q_pwp = self.env.now

        # Record where the patient is on the PwP WL
        self.step2_results_df.at[p.id, 'WL Posn'] = \
                                            g.number_on_pwp_wl
        self.step2_waiting_list.at[p.id, 'WL Position'] = g.number_on_pwp_wl

        if g.debug_level >=2:
            print(f'Patient sent down {p.step2_path_route}')

        while True:
            self.result = yield self.env.process(self.find_caseload_slot(p.step2_path_route))
            
            if self.result and isinstance(self.result, tuple) and len(self.result) == 2:
                self.pwp_caseload_id, self.pwp_caseload_res = self.result
                if self.pwp_caseload_res is not None:  # Ensure the resource is valid
                    break  # Exit the loop when a resource is found
            else:
                if g.debug_level >= 2:
                    print("No available resource found for PwP, retrying...")
            yield self.env.timeout(1)  # Wait a week and retry

            if self.result == (None, None):
                print(f"Stopping retry as no resources are available. Time: {self.env.now}")
                return  # **Exit function entirely**

        with self.pwp_caseload_res.get(1) as self.pwp_req:
            yield self.pwp_req

        # assign the caseload to the patient
        p.step3_resource_id = self.pwp_caseload_id

        if g.debug_level >=2:
            print(f'Resource {self.pwp_caseload_id} with a caseload remaining of {self.pwp_caseload_res.level} allocated to patient {p.id}')

        # # create a variable to store the current level of the caseload for this resource
        # self.pwp_caseload_posn = self.caseload_[f'{self.caseload_id}']
        # # add to this specific caseload
        # self.pwp_caseload_posn +=1

        if g.debug_level >=2:
            print(f'Patient {p.id} added to caseload {p.step2_resource_id} spaces left')

        # add to caseload
        g.number_on_pwp_cl += 1
        
        # as each patient reaches this stage take them off PwP wl
        g.number_on_pwp_wl -= 1
        # record the week that they started treatment
        p.step2_start_week = self.env.now

        # update waiting list info
        self.step2_waiting_list.at[p.id, 'IsWaiting'] = 0
        self.step2_waiting_list.at[p.id, 'End Week'] = self.env.now

        if g.debug_level >=2:
            print(f'{p.step2_path_route} RUNNER: Patient {p.id} removed from {p.step2_path_route} waiting list')

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step2_pwp_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) put through {p.step2_path_route}')

        #self.end_q_pwp = self.env.now
        # record how long they have waited to start treatment      
        self.q_time_pwp = p.step2_start_week - p.treat_wait_week
        if g.debug_level >=2:
            print(f'Patient {p.id} WEEK NUMBER {self.env.now} waited {self.q_time_pwp} weeks from {p.treat_wait_week} weeks to {p.step2_start_week} to enter {p.step2_path_route} treatment')

        self.step2_results_df.at[p.id, 'Route Name'] = p.step2_path_route
        self.step2_results_df.at[p.id, 'Run Number'] = self.run_number
        self.step2_results_df.at[p.id, 'Week Number'] = self.week_number
        # Calculate how long patient queued for PwP
        self.step2_results_df.at[p.id, 'Q Time'] = self.q_time_pwp

        # Generate a list of week numbers the patient is going to attend
        self.pwp_random_weeks = random.sample(range(self.week_number+1, self.week_number+g.step2_pwp_period), g.step2_pwp_sessions)

        # Add 1 at the start of the list
        self.pwp_random_weeks.insert(0, p.step2_start_week)

        # Optionally, sort the list to maintain sequential order
        self.pwp_random_weeks.sort()

        if g.debug_level >=2:
            print(f'Random Session week {len(self.pwp_random_weeks)} numbers are {self.pwp_random_weeks}')

        if g.debug_level >=2:
            print(f'Number of sessions is {g.step2_pwp_sessions}')

        # decide whether the DNA policy had been followed or not
        self.vary_dna_policy = random.uniform(0,1)

        if self.vary_dna_policy >= g.dna_policy_var:
            self.dnas_allowed = 2
        else:
            self.dnas_allowed = 3

        while self.pwp_session_counter < g.step2_pwp_sessions and self.pwp_dna_counter < self.dnas_allowed:

            if g.debug_level >= 2:
                print(f'FUNC PROCESS step2_pwp_process: Week {self.env.now}: Patient {p.id} '
                    f'(added week {p.week_added}) on {p.step2_path_route} '
                    f'Session {self.pwp_session_counter} on Week {self.pwp_random_weeks[self.pwp_session_counter]}')

            # Determine whether the session was DNA'd
            self.dna_pwp_session = random.uniform(0, 1)
            is_dna = 1 if self.dna_pwp_session <= g.step2_pwp_dna_rate else 0

            if is_dna:
                self.pwp_dna_counter += 1
                session_time = 0  # No session time if DNA'd
                admin_time = g.step2_session_admin
            else:
                session_time = g.step2_pwp_1st_mins if self.pwp_session_counter == 0 else g.step2_pwp_fup_mins
                admin_time = g.step2_session_admin

            # Determine if the patient is stepped up
            self.step_patient_up = random.uniform(0, 1)
            is_step_up = 1 if self.pwp_session_counter >= g.step2_pwp_sessions - 1 and self.step_patient_up <= g.step_up_rate else 0
            if is_step_up == 1:
                self.step2_results_df.at[p.id, 'IsStep'] = 1
            else:
                self.step2_results_df.at[p.id, 'IsStep'] = 0
            # Determine if the patient dropped out
            is_dropout = 1 if self.pwp_dna_counter >= self.dnas_allowed else 0
            if is_dropout == 1:
                self.step2_results_df.at[p.id, 'IsDropOut'] = 1
            else:
                self.step2_results_df.at[p.id, 'IsDropOut'] = 0
            # Store session results as a dictionary
            new_row = {
                        'Patient ID': p.id,
                        'Week Number': p.step3_start_week + self.pwp_random_weeks[self.pwp_session_counter],
                        'Run Number': self.run_number,
                        'Route Name': p.step2_path_route,
                        'Session Number': self.pwp_session_counter,
                        'Session Time': session_time,
                        'Admin Time': admin_time,
                        'IsDNA': is_dna
                    }

            # Append the session data to the DataFrame
            self.step2_sessions_df = pd.concat([self.step2_sessions_df, pd.DataFrame([new_row])], ignore_index=True)

            # Handle step-up logic
            if is_step_up:
                self.step2_results_df.at[p.id, 'IsStep'] = 1
                self.pwp_session_counter = 0
                self.pwp_dna_counter = 0  # Reset counters for the next step
                p.treat_wait_week = self.env.now
            
                if g.debug_level >= 2:
                    print(f'### STEPPED UP ###: Patient {p.id} has been stepped up, running Step3 route selector')
                yield self.env.process(self.patient_step3_pathway(p))

            # Handle dropout logic
            if is_dropout:
                self.step2_results_df.at[p.id, 'IsDropOut'] = 1
                if g.debug_level >= 2:
                    print(f'Patient {p.id} dropped out of {p.step2_path_route} treatment')
                p.step2_end_week = p.step2_start_week + self.pwp_random_weeks[self.pwp_session_counter]
                break  # Stop the loop if patient drops out

            # Move to the next session
            self.pwp_session_counter += 1

        if self.pwp_dna_counter >= self.dnas_allowed:

            self.env.process(self.record_caseload_use(p.step2_path_route,self.pwp_caseload_id,self.pwp_random_weeks[self.pwp_session_counter]))
            
        else:
            # record when the caseload resource can be restored
            self.env.process(self.record_caseload_use(p.step2_path_route,self.pwp_caseload_id,max(self.pwp_random_weeks)))
        
        # reset counters for pwp sessions
        self.pwp_session_counter = 0
        self.pwp_dna_counter = 0
        
        # take off caseload
        g.number_on_pwp_cl -=1
        
        yield self.env.timeout(0)
               
    def step2_group_process(self,patient):

        p = patient

        # counter for number of group sessions
        self.group_session_counter = 0
        # counter for applying DNA policy
        self.group_dna_counter = 0

        # Record where the patient is on the TA WL
        self.step2_results_df.at[p.id, 'WL Posn'] = \
                                            g.number_on_group_wl
        self.step2_waiting_list.at[p.id, 'WL Position'] = g.number_on_group_wl

        # Request a Group resource from the container
        with self.group_res.get(1) as group_req:
            yield group_req

        # add to caseload
        g.number_on_group_cl +=1

        # print(f'Patient {p} started Group')

        # as each patient reaches this stage take them off Group wl
        g.number_on_group_wl -= 1

        p.step2_start_week = self.env.now

        self.step2_waiting_list.at[p.id, 'IsWaiting'] = 0
        self.step2_waiting_list.at[p.id, 'End Week'] = self.env.now

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step2_group_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) put through {p.step2_path_route}')

        #self.end_q_group = self.env.now

        # Calculate how long patient queued for groups
        self.q_time_group = p.step2_start_week - p.treat_wait_week
        if g.debug_level >=2:
            print(f'Patient {p.id} WEEK NUMBER {self.env.now} waited {self.q_time_group} weeks from {p.treat_wait_week} weeks to {p.step2_start_week} to enter {p.step2_path_route} treatment')

        self.step2_results_df.at[p.id, 'Route Name'] = p.step2_path_route
        self.step2_results_df.at[p.id, 'Run Number'] = self.run_number
        self.step2_results_df.at[p.id, 'Week Number'] = self.week_number
        # Calculate how long patient queued for Group
        self.step2_results_df.at[p.id, 'Q Time'] = self.q_time_group

         # Generate a list of week numbers the patient is going to attend
        self.group_random_weeks = random.sample(range(self.week_number+1, self.week_number+10), g.step2_group_sessions)

        # Add 1 at the start of the list
        self.group_random_weeks.insert(0, p.step2_start_week)

        # Optionally, sort the list to maintain sequential order
        self.group_random_weeks.sort()

        if g.debug_level >=2:
            print(f'Random Session week {len(self.group_random_weeks)} numbers are {self.group_random_weeks}')

        if g.debug_level >=2:
            print(f'Number of sessions is {g.step2_group_sessions}')

        # decide whether the DNA policy had been followed or not
        self.vary_dna_policy = random.uniform(0,1)

        if self.vary_dna_policy >= g.dna_policy_var:
            self.dnas_allowed = 2
        else:
            self.dnas_allowed = 3

        while self.group_session_counter < g.step2_group_sessions and self.group_dna_counter < self.dnas_allowed:

            if g.debug_level >= 2:
                print(f'FUNC PROCESS step2_group_process: Week {self.env.now}: Patient {p.id} '
                    f'(added week {p.week_added}) on {p.step2_path_route} '
                    f'Session {self.group_session_counter} on Week {self.group_random_weeks[self.group_session_counter]}')

            # Determine whether the session was DNA'd
            self.dna_group_session = random.uniform(0, 1)
            is_dna = 1 if self.dna_group_session <= g.step2_group_dna_rate else 0

            if is_dna:
                self.group_dna_counter += 1
                session_time = 0  # No session time if DNA'd
                admin_time = g.step2_session_admin
            else:
                session_time = int(g.step2_group_session_mins/g.step2_group_size)
                admin_time = g.step2_session_admin

            # Determine if the patient is stepped up
            self.step_patient_up = random.uniform(0, 1)
            is_step_up = 1 if self.group_session_counter >= g.step2_group_sessions - 1 and self.step_patient_up <= g.step_up_rate else 0
            if is_step_up == 1:
                self.step2_results_df.at[p.id, 'IsStep'] = 1
            else:
                self.step2_results_df.at[p.id, 'IsStep'] = 0
            # Determine if the patient dropped out
            is_dropout = 1 if self.group_dna_counter >= self.dnas_allowed else 0
            if is_dropout == 1:
                self.step2_results_df.at[p.id, 'IsDropOut'] = 1
            else:
                self.step2_results_df.at[p.id, 'IsDropOut'] = 0

            # Store session results as a dictionary
            new_row = {
                        'Patient ID': p.id,
                        'Week Number': p.step3_start_week + self.group_random_weeks[self.group_session_counter],
                        'Run Number': self.run_number,
                        'Route Name': p.step2_path_route,
                        'Session Number': self.group_session_counter,
                        'Session Time': session_time,
                        'Admin Time': admin_time,
                        'IsDNA': is_dna
                    }

            # Append the session data to the DataFrame
            self.step2_sessions_df = pd.concat([self.step2_sessions_df, pd.DataFrame([new_row])], ignore_index=True)

            # Handle step-up logic
            if is_step_up:
                self.step2_results_df.at[p.id, 'IsStep'] = 1
                self.group_session_counter = 0
                self.group_dna_counter = 0  # Reset counters for the next step
                # record when they statted waiting i.e. at point of step up
                p.treat_wait_week = self.env.now
                if g.debug_level >= 2:
                    print(f'### STEPPED UP ###: Patient {p.id} has been stepped up, running Step3 route selector')
                yield self.env.process(self.patient_step3_pathway(p))

            # Handle dropout logic
            if is_dropout:
                self.step2_results_df.at[p.id, 'IsDropOut'] = 1
                if g.debug_level >= 2:
                    print(f'Patient {p.id} dropped out of {p.step2_path_route} treatment')
                p.step2_end_week = p.step2_start_week + self.group_random_weeks[self.group_session_counter]
                break  # Stop the loop if patient drops out

            # Move to the next session
            self.group_session_counter += 1

        # reset counters for group sessions
        self.group_session_counter = 0
        self.group_dna_counter = 0
        
        # take off caseload
        g.number_on_group_cl -=1
              
        yield self.env.timeout(self.group_session_counter)

    def step3_cbt_process(self,patient):

        p = patient

        # counter for number of couns sessions
        self.cbt_session_counter = 0
        # counter for applying DNA policy
        self.cbt_dna_counter = 0

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} added to {p.step3_path_route} waiting list')

        start_q_couns = self.env.now

        # Record where the patient is on the couns WL
        self.step3_results_df.at[p.id, 'WL Posn'] = \
                                            g.number_on_cbt_wl
        self.step3_waiting_list.at[p.id, 'WL Position'] = g.number_on_cbt_wl

        # Check if there is a caseload slot available and return the resource
        while True:
            self.result = yield self.env.process(self.find_caseload_slot(p.step3_path_route))
            
            if self.result and isinstance(self.result, tuple) and len(self.result) == 2:
                self.cbt_caseload_id, self.cbt_caseload_res = self.result
                if self.cbt_caseload_res is not None:  # Ensure the resource is valid
                    break  # Exit the loop when a resource is found
            else:
                if g.debug_level >= 2:
                    print("No available resource found for Couns, retrying...")

            if self.result == (None, None):
                print(f"Stopping retry as no resources are available. Time: {self.env.now}")
                return  # **Exit function entirely**

            yield self.env.timeout(1)  # Wait a week and retry

        with self.cbt_caseload_res.get(1) as self.cbt_req:
            yield self.cbt_req

        # assign the caseload to the patient
        p.step3_resource_id = self.cbt_caseload_id

        # if g.debug_level >=2:
        #     print(f'Resource {self.cbt_caseload_id} with a caseload remaining of {self.cbt_caseload_res.level} allocated to patient {p.id}')

        # # create a variable to store the current level of the caseload for this resource
        # self.pwp_caseload_posn = self.caseload_[f'{self.caseload_id}']
        # # add to this specific caseload
        # self.pwp_caseload_posn +=1

        # if g.debug_level >=2:
        #     print(f'Patient {p.id} added to caseload {p.step3_resource_id}, {self.cbt_resources[p.step3_resource_id].level} spaces left')

        # add to overall caseload
        g.number_on_cbt_cl +=1

        # print(f'Patient {p} started couns')

        # as each patient reaches this stage take them off couns WL
        g.number_on_cbt_wl -= 1

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} removed from {p.step3_path_route} waiting list')

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step3_cbt_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) put through {p.step3_path_route}')

        end_q_cbt = self.env.now

        p.step3_start_week = self.week_number

        self.step3_waiting_list.at[p.id, 'IsWaiting'] = 0
        self.step3_waiting_list.at[p.id, 'End Week'] = self.env.now

        # Calculate how long patient queued for couns
        self.q_time_cbt = p.step3_start_week - p.treat_wait_week

        if g.debug_level >=2:
            print(f'Patient {p.id} WEEK NUMBER {self.env.now} waited {self.q_time_cbt} weeks from {p.treat_wait_week} weeks to {p.step3_start_week} to enter {p.step3_path_route} treatment')
        self.step3_results_df.at[p.id, 'Route Name'] = p.step3_path_route
        self.step3_results_df.at[p.id, 'Run Number'] = self.run_number
        self.step3_results_df.at[p.id, 'Week Number'] = self.week_number
        # Calculate how long patient queued for PwP
        self.step3_results_df.at[p.id, 'Q Time'] = self.q_time_cbt
        
        # decide whether the DNA policy had been followed or not
        self.vary_dna_policy = random.uniform(0,1)

        if self.vary_dna_policy >= g.dna_policy_var:
            self.dnas_allowed = 2
        else:
            self.dnas_allowed = 3

        # decide whether the number of sessions is going to be varied from standard
        self.vary_step3_sessions = random.uniform(0,1)

        self.random_num_sessions = 0

        self.random_num_sessions += vary_number_sessions(13,35)

        if self.vary_step3_sessions >= g.step_3_session_var:
            self.number_cbt_sessions = g.step3_cbt_sessions
            self.step3_cbt_period = g.step3_cbt_period
        else:
            self.number_cbt_sessions = self.random_num_sessions
            self.step3_cbt_period = g.step3_cbt_period+(self.random_num_sessions*2)

        # Generate a list of week numbers the patient is going to attend
        self.cbt_random_weeks = random.sample(range(self.week_number+1, self.week_number+(self.step3_cbt_period*2)), self.number_cbt_sessions)

        # Add 1 at the start of the list
        self.cbt_random_weeks.insert(0, p.step3_start_week)

        # sort the list to maintain sequential order
        self.cbt_random_weeks.sort()

        if self.cbt_session_counter < len(self.cbt_random_weeks):
            p.step3_end_week = p.step3_start_week + self.cbt_random_weeks[self.cbt_session_counter]
        else:
            if g.debug_level >=2:
                print(f"Warning: Index {self.cbt_session_counter} out of range for cbt_random_weeks.")

        if g.debug_level >=2:
            print(f'Random Session week {len(self.cbt_random_weeks)} numbers are {self.cbt_random_weeks}')

        if g.debug_level >=2:
            print(f'Number of sessions is {self.number_cbt_sessions}')

        # print(self.random_weeks)

        while self.cbt_session_counter < g.step3_cbt_sessions and self.cbt_dna_counter < self.dnas_allowed:

            if g.debug_level >= 2:
                print(f'FUNC PROCESS step3_cbt_process: Week {self.env.now}: Patient {p.id} '
                    f'(added week {p.week_added}) on {p.step3_path_route} '
                    f'Session {self.cbt_session_counter} on Week {self.cbt_random_weeks[self.cbt_session_counter]}')

            # Determine whether the session was DNA'd
            self.dna_cbt_session = random.uniform(0, 1)
            is_dna = 1 if self.dna_cbt_session <= g.step3_cbt_dna_rate else 0

            if is_dna:
                self.cbt_dna_counter += 1
                session_time = 0  # No session time if DNA'd
                admin_time = g.step3_session_admin
            else:
                session_time = g.step3_cbt_1st_mins if self.cbt_session_counter == 0 else g.step3_cbt_fup_mins
                admin_time = g.step3_session_admin

            # Determine if the patient is stepped up
            self.step_patient_down = random.uniform(0, 1)
            is_step_down = 1 if self.cbt_session_counter >= g.step3_cbt_sessions - 1 and self.step_patient_down <= g.step_down_rate else 0
            if is_step_down == 1:
                self.step3_results_df.at[p.id, 'IsStep'] = 1
            else:
                self.step3_results_df.at[p.id, 'IsStep'] = 0
            # Determine if the patient dropped out
            is_dropout = 1 if self.cbt_dna_counter >= self.dnas_allowed else 0
            if is_dropout == 1:
                self.step3_results_df.at[p.id, 'IsDropOut'] = 1
            else:
                self.step3_results_df.at[p.id, 'IsDropOut'] = 0

            # Store session results as a dictionary
            new_row = {
                        'Patient ID': p.id,
                        'Week Number': p.step3_start_week + self.cbt_random_weeks[self.cbt_session_counter],
                        'Run Number': self.run_number,
                        'Route Name': p.step3_path_route,
                        'Session Number': self.cbt_session_counter,
                        'Session Time': session_time,
                        'Admin Time': admin_time,
                        'IsDNA': is_dna
                    }

            # Append the session data to the DataFrame
            self.step3_sessions_df = pd.concat([self.step3_sessions_df, pd.DataFrame([new_row])], ignore_index=True)

            # Handle step-up logic
            if is_step_down:
                self.step3_results_df.at[p.id, 'IsStep'] = 1
                self.cbt_session_counter = 0
                self.cbt_dna_counter = 0  # Reset counters for the next step
                p.treat_wait_week = self.env.now
                if g.debug_level >= 2:
                    print(f'### STEPPED UP ###: Patient {p.id} has been stepped up, running Step3 route selector')
                yield self.env.process(self.patient_step2_pathway(p))

            # Handle dropout logic
            if is_dropout:
                self.step3_results_df.at[p.id, 'IsDropOut'] = 1
                if g.debug_level >= 2:
                    print(f'Patient {p.id} dropped out of {p.step3_path_route} treatment')
                p.step3_end_week = p.step3_start_week + self.cbt_random_weeks[self.cbt_session_counter]
                break  # Stop the loop if patient drops out

            # Move to the next session
            self.cbt_session_counter += 1

        # # remove from this specific caseload
        # self.cbt_caseload_posn -=1

        if self.cbt_dna_counter >= self.dnas_allowed:

            self.env.process(self.record_caseload_use(p.step3_path_route,self.cbt_caseload_id,self.cbt_random_weeks[self.cbt_session_counter]))
            
        else:
            # record when the caseload resource can be restored
            self.env.process(self.record_caseload_use(p.step3_path_route,self.cbt_caseload_id,max(self.cbt_random_weeks)))
        
        # reset counters for pwp sessions
        self.cbt_session_counter = 0
        self.cbt_dna_counter = 0
        
        # take off caseload
        g.number_on_cbt_cl -=1
        
        yield self.env.timeout(0)

    def step3_couns_process(self,patient):

        p = patient

        # counter for number of couns sessions
        self.couns_session_counter = 0
        # counter for applying DNA policy
        self.couns_dna_counter = 0

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} added to {p.step3_path_route} waiting list')

        start_q_couns = self.env.now

        # Record where the patient is on the couns WL
        self.step3_results_df.at[p.id, 'WL Posn'] = \
                                            g.number_on_couns_wl
        self.step2_waiting_list.at[p.id, 'WL Position'] = g.number_on_couns_wl

        # Check if there is a caseload slot available and return the resource
        while True:
            self.result = yield self.env.process(self.find_caseload_slot(p.step3_path_route))
            
            if self.result and isinstance(self.result, tuple) and len(self.result) == 2:
                self.couns_caseload_id, self.couns_caseload_res = self.result
                if self.couns_caseload_res is not None:  # Ensure the resource is valid
                    break  # Exit the loop when a resource is found
            else:
                if g.debug_level >= 2:
                    print("No available resource found for Couns, retrying...")

            if self.result == (None, None):
                print(f"Stopping retry as no resources are available. Time: {self.env.now}")
                return  # **Exit function entirely**

            yield self.env.timeout(1)  # Wait a week and retry

        with self.couns_caseload_res.get(1) as self.couns_req:
            yield self.couns_req

        # assign the caseload to the patient
        p.step3_resource_id = self.couns_caseload_id

        # if g.debug_level >=2:
        #     print(f'Resource {self.couns_caseload_id} with a caseload remaining of {self.couns_caseload_res.level} allocated to patient {p.id}')

        # # create a variable to store the current level of the caseload for this resource
        # self.pwp_caseload_posn = self.caseload_[f'{self.caseload_id}']
        # # add to this specific caseload
        # self.pwp_caseload_posn +=1

        # if g.debug_level >=2:
        #     print(f'Patient {p.id} added to caseload {p.step3_resource_id}, {self.couns_resources[p.step3_resource_id].level} spaces left')

        # add to overall caseload
        g.number_on_couns_cl +=1

        # print(f'Patient {p} started couns')

        # as each patient reaches this stage take them off couns WL
        g.number_on_couns_wl -= 1

        if g.debug_level >=2:
            print(f'{p.step3_path_route} RUNNER: Patient {p.id} removed from {p.step3_path_route} waiting list')

        if g.debug_level >= 2:
            print(f'FUNC PROCESS step3_couns_process: Week {self.env.now}: Patient {p.id} (added week {p.week_added}) put through {p.step3_path_route}')

        end_q_couns = self.env.now

        p.step3_start_week = self.week_number

        self.step3_waiting_list.at[p.id, 'IsWaiting'] = 0
        self.step3_waiting_list.at[p.id, 'End Week'] = self.env.now

        # Calculate how long patient queued for couns
        self.q_time_couns = p.step3_start_week - p.treat_wait_week

        if g.debug_level >=2:
            print(f'Patient {p.id} WEEK NUMBER {self.env.now} waited {self.q_time_couns} weeks from {p.treat_wait_week} weeks to {p.step3_start_week} to enter {p.step3_path_route} treatment')
        self.step3_results_df.at[p.id, 'Route Name'] = p.step3_path_route
        self.step3_results_df.at[p.id, 'Run Number'] = self.run_number
        self.step3_results_df.at[p.id, 'Week Number'] = self.week_number
        # Calculate how long patient queued for PwP
        self.step3_results_df.at[p.id, 'Q Time'] = self.q_time_couns
        
        # decide whether the DNA policy had been followed or not
        self.vary_dna_policy = random.uniform(0,1)

        if self.vary_dna_policy >= g.dna_policy_var:
            self.dnas_allowed = 2
        else:
            self.dnas_allowed = 3

        # decide whether the number of sessions is going to be varied from standard
        self.vary_step3_sessions = random.uniform(0,1)

        self.random_num_sessions = 0

        self.random_num_sessions += vary_number_sessions(8,22)

        if self.vary_step3_sessions >= g.step_3_session_var:
            self.number_couns_sessions = g.step3_couns_sessions
            self.step3_couns_period = g.step3_couns_period
        else:
            self.number_couns_sessions = self.random_num_sessions
            self.step3_couns_period = g.step3_couns_period+(self.random_num_sessions*2)

        # Generate a list of week numbers the patient is going to attend
        self.couns_random_weeks = random.sample(range(self.week_number+1, self.week_number+(self.step3_couns_period*2)), self.number_couns_sessions)

        # Add 1 at the start of the list
        self.couns_random_weeks.insert(0, p.step3_start_week)

        # sort the list to maintain sequential order
        self.couns_random_weeks.sort()

        if self.couns_session_counter < len(self.couns_random_weeks):
            p.step3_end_week = p.step3_start_week + self.couns_random_weeks[self.couns_session_counter]
        else:
            if g.debug_level >=2:
                print(f"Warning: Index {self.couns_session_counter} out of range for couns_random_weeks.")

        if g.debug_level >=2:
            print(f'Random Session week {len(self.couns_random_weeks)} numbers are {self.couns_random_weeks}')

        if g.debug_level >=2:
            print(f'Number of sessions is {self.number_couns_sessions}')

        # print(self.random_weeks)

        while self.couns_session_counter < g.step3_couns_sessions and self.couns_dna_counter < self.dnas_allowed:

            if g.debug_level >= 2:
                print(f'FUNC PROCESS step3_couns_process: Week {self.env.now}: Patient {p.id} '
                    f'(added week {p.week_added}) on {p.step3_path_route} '
                    f'Session {self.couns_session_counter} on Week {self.couns_random_weeks[self.couns_session_counter]}')

            # Determine whether the session was DNA'd
            self.dna_couns_session = random.uniform(0, 1)
            is_dna = 1 if self.dna_couns_session <= g.step3_couns_dna_rate else 0

            if is_dna:
                self.couns_dna_counter += 1
                session_time = 0  # No session time if DNA'd
                admin_time = g.step3_session_admin
            else:
                session_time = g.step3_couns_1st_mins if self.couns_session_counter == 0 else g.step3_couns_fup_mins
                admin_time = g.step3_session_admin

            # Determine if the patient is stepped up
            self.step_patient_down = random.uniform(0, 1)
            is_step_down = 1 if self.couns_session_counter >= g.step3_couns_sessions - 1 and self.step_patient_down <= g.step_down_rate else 0
            if is_step_down == 1:
                self.step3_results_df.at[p.id, 'IsStep'] = 1
            else:
                self.step3_results_df.at[p.id, 'IsStep'] = 0
            # Determine if the patient dropped out
            is_dropout = 1 if self.couns_dna_counter >= self.dnas_allowed else 0
            if is_dropout == 1:
                self.step3_results_df.at[p.id, 'IsDropOut'] = 1
            else:
                self.step3_results_df.at[p.id, 'IsDropOut'] = 0

            # Store session results as a dictionary
            new_row = {
                        'Patient ID': p.id,
                        'Week Number': p.step3_start_week + self.couns_random_weeks[self.couns_session_counter],
                        'Run Number': self.run_number,
                        'Route Name': p.step3_path_route,
                        'Session Number': self.couns_session_counter,
                        'Session Time': session_time,
                        'Admin Time': admin_time,
                        'IsDNA': is_dna
                    }

            # Append the session data to the DataFrame
            self.step3_sessions_df = pd.concat([self.step3_sessions_df, pd.DataFrame([new_row])], ignore_index=True)

            # Handle step-up logic
            if is_step_down:
                self.step3_results_df.at[p.id, 'IsStep'] = 1
                self.couns_session_counter = 0
                self.couns_dna_counter = 0  # Reset counters for the next step
                p.treat_wait_week = self.env.now
                if g.debug_level >= 2:
                    print(f'### STEPPED UP ###: Patient {p.id} has been stepped up, running Step3 route selector')
                yield self.env.process(self.patient_step2_pathway(p))

            # Handle dropout logic
            if is_dropout:
                self.step3_results_df.at[p.id, 'IsDropOut'] = 1
                if g.debug_level >= 2:
                    print(f'Patient {p.id} dropped out of {p.step3_path_route} treatment')
                p.step3_end_week = p.step3_start_week + self.couns_random_weeks[self.couns_session_counter]
                break  # Stop the loop if patient drops out


            # Move to the next session
            self.couns_session_counter += 1

        # # remove from this specific caseload
        # self.couns_caseload_posn -=1

        if self.couns_dna_counter >= self.dnas_allowed:

            self.env.process(self.record_caseload_use(p.step3_path_route,self.couns_caseload_id,self.couns_random_weeks[self.couns_session_counter]))
            
        else:
            # record when the caseload resource can be restored
            self.env.process(self.record_caseload_use(p.step3_path_route,self.couns_caseload_id,max(self.couns_random_weeks)))
        
        # reset counters for pwp sessions
        self.couns_session_counter = 0
        self.couns_dna_counter = 0
        
        # take off caseload
        g.number_on_couns_cl -=1
        
        yield self.env.timeout(0)

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
        g.number_on_ta_wl = 0
        g.number_on_pwp_cl = 0
        g.number_on_group_cl = 0
        g.number_on_cbt_cl = 0
        g.number_on_couns_cl = 0

    # The run method starts up the DES entity generators, runs the simulation,
    # and in turns calls anything we need to generate results for the run
    def run(self, print_run_results=True):

        # create a simpy store for this run to hold the patients until the group 
        # has enough members. This will persist for an entire run has finished 
        # and patients will be added to it and taken out of it as groups fill up 
        # and are run
        self.group_store = simpy.Store(
                                        self.env,
                                        capacity=g.step2_group_size
                                        )
        #self.pwp_res_list = {}

        # Start up the week to start processing patients
        self.env.process(self.the_governor())

        # Run the model
        self.env.run()

        # Now the simulation run has finished, call the method that calculates
        # run results
        self.calculate_run_results()

        return self.step2_results_df, self.step3_results_df, self.step2_sessions_df, self.step3_sessions_df

        # Print the run number with the patient-level results from this run of
        # the model
        if print_run_results:
            #print(g.weekly_wl_posn)
            print (f"Run Number {self.run_number}")
            print (self.asst_results_df)

# Class representing a Trial for our simulation - a batch of simulation runs.
class Trial:
    def __init__(self):
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
        self.step2_waiting_dfs = []
        self.step3_waiting_dfs = []
        self.staff_weekly_dfs = []

    def run_trial(self):

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

            my_model.step2_results_df = pd.DataFrame(my_model.step2_results_df)
            my_model.step2_sessions_df = pd.DataFrame(my_model.step2_sessions_df)
            my_model.step3_results_df = pd.DataFrame(my_model.step3_results_df)
            my_model.step3_sessions_df = pd.DataFrame(my_model.step3_sessions_df)

            if run == 0:
                self.step2_results_df = my_model.step2_results_df.copy()
                self.step3_results_df = my_model.step3_results_df.copy()
                self.step2_sessions_df = my_model.step2_sessions_df.copy()
                self.step3_sessions_df = my_model.step3_sessions_df.copy()
            else:
                self.step2_results_df = pd.concat([self.step2_results_df, my_model.step2_results_df])
                self.step3_results_df = pd.concat([self.step3_results_df, my_model.step3_results_df])
                self.step2_sessions_df = pd.concat([self.step2_sessions_df, my_model.step2_sessions_df])
                self.step3_sessions_df = pd.concat([self.step3_sessions_df, my_model.step3_sessions_df])


            my_model.asst_weekly_stats = pd.DataFrame(my_model.asst_weekly_stats)
            my_model.step2_weekly_stats = pd.DataFrame(my_model.step2_weekly_stats)
            my_model.step3_weekly_stats = pd.DataFrame(my_model.step3_weekly_stats)
            my_model.step2_waiting_stats = pd.DataFrame(my_model.step2_waiting_stats)
            my_model.step3_waiting_stats = pd.DataFrame(my_model.step3_waiting_stats)
            my_model.staff_weekly_stats = pd.DataFrame(my_model.staff_weekly_stats)

            my_model.asst_weekly_stats['Run'] = run
            my_model.step2_waiting_stats['Run'] = run
            my_model.step3_waiting_stats['Run'] = run
            my_model.step2_weekly_stats['Run'] = run
            my_model.step3_weekly_stats['Run'] = run
            my_model.staff_weekly_stats['Run'] = run

            self.asst_weekly_dfs.append(my_model.asst_weekly_stats)
            self.step2_waiting_dfs.append(my_model.step2_waiting_stats)
            self.step3_waiting_dfs.append(my_model.step3_waiting_stats)
            self.step2_weekly_dfs.append(my_model.step2_weekly_stats)
            self.step3_weekly_dfs.append(my_model.step3_weekly_stats)
            self.staff_weekly_dfs.append(my_model.staff_weekly_stats)

            if run == 0:
                self.caseload_weekly_dfs = pd.json_normalize(g.caseload_weekly_stats, 'Data', ['Run Number', 'Week Number'])
            else:
                self.caseload_weekly_dfs = pd.concat([
                    self.caseload_weekly_dfs,
                    pd.json_normalize(g.caseload_weekly_stats, 'Data', ['Run Number', 'Week Number'])
                ])

        return (
            self.step2_results_df, 
            self.step2_sessions_df, 
            self.step3_results_df,
            self.step3_sessions_df,
            pd.concat(self.asst_weekly_dfs) if self.asst_weekly_dfs else pd.DataFrame(),
            pd.concat(self.step2_waiting_dfs) if self.step2_waiting_dfs else pd.DataFrame(),
            pd.concat(self.step3_waiting_dfs) if self.step3_waiting_dfs else pd.DataFrame(),
            pd.concat(self.staff_weekly_dfs) if self.staff_weekly_dfs else pd.DataFrame(),
            self.caseload_weekly_dfs if hasattr(self, 'caseload_weekly_dfs') else pd.DataFrame()
        )

if __name__ == "__main__":
    my_trial = Trial()
    step2_results_df, step2_sessions_df, step3_results_df, step3_sessions_df, asst_weekly_dfs, step2_waiting_dfs, step3_waiting_dfs, staff_weekly_dfs, caseload_weekly_dfs  = my_trial.run_trial()

    # print(df_trial_results)
    # step2_waiting_dfs.to_csv("step2_waiters.csv", index=True)
    # step3_waiting_dfs.to_csv("step3_waiters.csv", index=True)
    # step2_results_df.to_csv("step2_results.csv", index=True)
    # caseload_weekly_dfs.to_csv("caseloads.csv", index=True)
    #step2_results_df, step3_results_df, df_trial_results, asst_weekly_dfs, step2_weekly_dfs, step3_weekly_dfs, staff_weekly_dfs, caseload_weekly_dfs  = my_trial.run_trial()

#df_trial_results, print(asst_weekly_dfs.to_string()), print(step2_weekly_dfs.to_string()), print(step3_weekly_dfs.to_string()), staff_weekly_dfs, print(caseload_weekly_dfs.to_string())

# asst_weekly_dfs.to_csv('S:\Departmental Shares\IM&T\Information\Business Intelligence\Heath McDonald\HSMA\Discrete Event Simulations\IAPT DES\asst_weekly_summary.csv')
# step2_weekly_dfs.to_csv('step2_weekly_summary.csv')
# step3_weekly_dfs.to_csv('step3_weekly_summary.csv')
# caseload_weekly_dfs.to_csv('caseload_weekly_summary.csv')

#S:\Departmental Shares\IM&T\Information\Business Intelligence\Heath McDonald\HSMA\Discrete Event Simulations\IAPT DES


