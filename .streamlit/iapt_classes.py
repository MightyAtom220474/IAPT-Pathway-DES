import simpy
import random
import numpy as np
import pandas as pd

class g:

    # used for testing
    debug_level = 2

    # Referrals
    mean_referrals_pw = 60

    # Screening
    referral_rej_rate = 0.3 # % of referrals rejected, advised 30%
    referral_review_rate = 0.4 # % that go to MDT as prev contact with Trust
    mdt_freq = 2 # how often in weeks MDT takes place, longest time a review referral may wait for review
    review_rej_rate = 0.5 # % ref that got to MDT and get rejected
    base_waiting_list = 2741 # current number of patients on waiting list
    referral_screen_time = 15 # average time it takes to screen one referral
    opt_in_wait = 1 # no. of weeks patients have to opt in
    opt_in_qtime = 4 # longest period a patient will wait for tel assessment based on 4 week window for asst slots
    opt_in_rate = 0.75 # % of referrals that opt-in
    asst_6_weeks = 0.9 # % of referrals that are assessed within 6 weeks
    ta_accept_rate = 0.75 ##### assume 75% of TA's accepted, need to check this #####

    # Step 2
    step2_ratio = 0.85 # proportion of patients that go onto Step2 vs Step3
    step2_routes = ['PwP','Dep','CBT'] # possible Step2 routes
    step2_path_ratios = [0.4,0.3,0.3] # Step2 proportion for each route
    step2_pwp_sessions = 6 # number of PwP sessions at Step2
    step2_pwp_period = 16 # max number of weeks PwP delivered over
    step2_group_range = [6,12] # range of possible group sessions
    step2_asst_admin = 15 # number of mins of clinical admin per session


    # Step Moves
    step_up_rate = 0.05 # proportion of Step2 that get stepped up
    step_down_rate = 0.003 # proportion of Step3 that get stepped down

    # Step 3
    step3_ratio = 0.15 # proportion of patients that go onto Step3 vs Step2
    step3_routes = ['PfCBT','Group','CBT','EMDR','DepC','DIT','IPT','CDEP'] # possible Step2 routes
    step3_path_ratios = [0.1,0.25,0.25,0.05,0.05,0.1,0.1,0.1] # Step3 proportion for each route ##### Need to clarify exact split

    # Staff
    supervision_time = 120 # 2 hours per month per modality ##### could use modulus for every 4th week
    break_time = 100 # 20 mins per day
    wellbeing_time = 120 # 2 hours allocated per month
    counsellors_huddle = 120 # 30 hrs p/w or 1 hr per fortnight
    cpd_time = 225 # half day per month CPD

    # Job Plans
    number_staff_cbt = 9.0
    number_staff_couns = 10.0
    number_staff_pwp = 10.0
    hours_avail_cbt = 22.0
    hours_avail_couns = 22.0
    hours_avail_pwp = 21.0

    # Simulation
    sim_duration = 52
    number_of_runs = 10
    std_dev = 3 # used for randomising activity times

    # Result storage
    all_results = []
    weekly_wl_posn = pd.DataFrame() # container to hold w/l position at end of week
    number_on_triage_wl = 0 # used to keep track of triage WL position
    number_on_mdt_wl = 0 # used to keep track of MDT WL position
    number_on_asst_wl = 0 # used to keep track of asst WL position

    # bring in past referral data
    referral_rate_lookup = pd.read_csv('talking_therapies_referral_rates.csv'
                                                                ,index_col=0)
    #print(referral_rate_lookup)
    
# Patient to capture flow of patient through pathway
class Patient:
    def __init__(self, p_id):
        # Patient
        self.id = p_id
        self.patient_at_risk # used to determine DNA/Canx policy to apply

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

        
        # Step2
        self.step2_path_route = [] # string, which Step2 path they took
        self.step2_place_on_wl = 0 # position they are on Step2 waiting list
        self.step2_session_count = 0 # counter for no. of sessions have had
        self.step2_drop_out = 0 # did they drop out during Step2
        self.step2_week_number = 0 # counter for which week number they are on

        # Step3
        self.step3_path_route = [] # string, which Step2 path they took
        self.step3_place_on_wl = 0 # position they are on Step2 waiting list
        self.step3_session_count = 0 # counter for no. of sessions have had
        self.step3_drop_out = 0 # did they drop out during Step2
        self.step3_week_number = 0 # counter for which week number they are on
        
# Staff class to be run weekly by week runner to record staff non-clinical time
class Staff:
    def __init__(self, s_id):
        
        # Staff attributes
        self.id = s_id
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
        self.asst_results_df['Referral Time Screen'] = [0.0] # time in mins taken to screen referral
        self.asst_results_df['Referral Rejected'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Referral Reviewed'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Review Wait'] = [0.0] # time between screening and getting review
        self.asst_results_df['Review Rejected'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Opted In'] = [0] # 1 = Yes, 0 = No
        self.asst_results_df['Opt-in Wait'] = [0.0] # time between opt-in notification and patient opting in
        self.asst_results_df['Opt-in Q Time'] = [0.0] # time between opting in and actual TA, 4 week window
        self.asst_results_df['TA Outcome'] = [0] # 1 = Accepted, 0 = Rejected

        # Indexing
        self.asst_results_df.set_index("Patient ID", inplace=True) 

        # Step2
        # Create a new DataFrame that will store opt-in results against the patient ID
        self.step2_results_df = pd.DataFrame()
        
        self.step2_results_df['Patient ID'] = [1]
        self.step2_results_df['Week Number'] = [0]
        self.step2_results_df['Run Number'] = [0]
        self.step2_results_df['Step2 Route'] = [] # which Step2 pathway the patient was sent down
        self.step2_results_df['Session Number'] = [0]
        self.step2_results_df['Session Time'] = [0.0]
        self.step2_results_df['Session Attendance'] = [0]

        # Indexing
        self.step2_results_df.set_index("Patient ID", inplace=True) 

        # Step3
        # Create a new DataFrame that will store Step3 results against the patient ID
        # Create a new DataFrame that will store opt-in results against the patient ID
        self.step3_results_df = pd.DataFrame()
        
        self.step3_results_df['Patient ID'] = [1]
        self.step3_results_df['Week Number'] = [0]
        self.step3_results_df['Run Number'] = [0]
        self.step3_results_df['Step2 Route'] = [] # which Step2 pathway the patient was sent down
        self.step3_results_df['Session Number'] = [0]
        self.step3_results_df['Session Time'] = [0.0]
        self.step3_results_df['Session Attendance'] = [0]
        
        # Indexing
        self.step3_results_df.set_index("Patient ID", inplace=True) 

    # random number generator for activity times
    def random_normal(self, mean, std_dev):
        while True:
            activity_time = random.gauss(mean, std_dev)
            if activity_time > 0:
                return activity_time

    def week_runner(self,number_of_weeks):

        # week counter
        self.week_number = 0

        # list to hold weekly asst statistics
        self.asst_weekly_stats = []
        # list to hold weekly Step2 statistics
        #self.step2_weekly_stats = []
        # list to hold weekly Step3 statistics
        #self.step3_weekly_stats = []

        while self.week_number <= number_of_weeks:
            if g.debug_level >= 1:
                print(
                    f"""
    ##################################
    # Week {self.week_number}
    ##################################
                    """
                    )
            
            # Start up the referral generator function
            self.env.process(self.generator_patient_referrals())

            ########## need to start up the generator for non-clinical time here too ##########

            self.ref_tot_screen = self.asst_results_df[
                                                'Referral Time Screen'].sum()
            self.ref_tot_reject = self.asst_results_df[
                                                'Referral Rejected'].sum()
            self.ref_optin_delay = self.asst_results_df['Opt-in Wait'].mean()
            self.ref_tot_optin = self.asst_results_df['Opted In'].sum()
            self.ref_optin_wait = self.asst_results_df['Opt-in Q Time'].mean()
            self.asst_tot_accept = self.asst_results_df['TA Outcome'].sum()
            
            # self.max_triage_wl = self.results_df["Triage WL Posn"].max()
            # self.triage_rej = self.results_df["Triage Rejected"].sum()
            # self.triage_avg_wait = self.results_df["Q Time Triage"].mean()
            # self.triage_tot_clin = self.results_df['Triage Mins Clin'].sum()
            # self.triage_tot_admin = self.results_df['Triage Mins Admin'].sum()
            # self.triage_tot_reject = self.results_df['Triage Time Reject'].sum()
            # self.pack_tot_send = self.results_df["Time Pack Send"].sum()
            # self.pack_rej = self.results_df["Pack Rejected"].sum()
            # self.pack_tot_rej = self.results_df["Time Pack Reject"].sum()
            # self.obs_tot_visit = self.results_df["Time Obs Visit"].sum()
            # self.obs_rej = self.results_df["Obs Rejected"].sum()
            # self.obs_tot_rej = self.results_df["Time Obs Reject"].sum()
            # self.mdt_tot_prep = self.results_df["Time Prep MDT"].sum()
            # self.mdt_tot_meet = self.results_df["Time Meet MDT"].sum()
            # self.max_mdt_wl = self.results_df["MDT WL Posn"].max()
            # self.mdt_tot_rej = self.results_df["MDT Time Reject"].sum()
            # self.mdt_rej = self.results_df["MDT Rejected"].sum()
            # self.mdt_avg_wait = self.results_df["Q Time MDT"].mean()
            # #self.mdt_targ_wait = g.target_mdt_wait
            # self.max_asst_wl = self.results_df["Asst WL Posn"].max()
            # self.asst_rej = self.results_df["Asst Rejected"].sum()
            # self.asst_avg_wait = self.results_df["Q Time Asst"].mean()
            # self.asst_tot_clin = self.results_df['Asst Mins Clin'].sum()
            # self.asst_tot_admin = self.results_df['Asst Mins Admin'].sum()
            # self.diag_tot_rej = self.results_df['Diag Rejected Time'].sum()
            # self.diag_tot_acc = self.results_df['Diag Accepted Time'].sum()
            #self.asst_targ_wait = g.target_asst_wait

            # weekly waiting list positions
            self.asst_weekly_stats.append(
                {
                 'Week Number':self.week_number,
                 'Referral Screen Mins':self.ref_total_screen,   
                 'Referrals Rejected':self.ref_tot_reject,
                 'Referrals Delay Opt-in':self.ref_optin_delay,
                 'Referrals Opted-in':self.ref_tot_optin,
                 'Referrals Wait Opt-in':self.ref_optin_wait,
                 'TA Total Accept':self.asst_tot_accept,
                #  'Triage Reject Mins':self.triage_tot_reject,
                #  'Pack Send Mins':self.pack_tot_send,
                #  'Pack Rejects':self.pack_rej,
                #  'Pack Reject Mins':self.pack_tot_rej,
                #  'Obs Visit Mins':self.obs_tot_visit,
                #  'Obs Rejects':self.obs_rej,
                #  'Obs Reject Mins':self.obs_tot_rej,
                #  'MDT Prep Mins':self.mdt_tot_prep,
                #  'MDT Meet Mins':self.mdt_tot_meet,
                #  'MDT WL':self.max_mdt_wl,
                #  'MDT Rejects':self.mdt_rej,
                #  'MDT Reject Mins':self.mdt_tot_rej,
                #  'MDT Wait':self.mdt_avg_wait,
                #  'Asst WL':self.max_asst_wl,
                #  'Asst Rejects':self.asst_rej,
                #  'Asst Wait':self.asst_avg_wait,
                #  'Asst Clin Mins':self.asst_tot_clin,
                #  'Asst Admin Mins':self.asst_tot_admin,
                #  'Diag Reject Mins':self.diag_tot_rej,
                #  'Diag Accept Mins':self.diag_tot_acc,
                }
                )
            
            
            # replenish resources
            asst_amount_to_fill = g.asst_resource - self.triage_res.level
            step2_amount_to_fill = g.mdt_resource - self.step2_res.level
            step3_amount_to_fill = g.asst_resource - self.step3_res.level

            if asst_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"Asst Level: {self.asst_res.level}")
                    print(f"Putting in {asst_amount_to_fill}")

                self.asst_res.put(asst_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New Asst Level: {self.asst_res.level}")

            if step2_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"Step2 Level: {self.step2_res.level}")
                    print(f"Putting in {step2_amount_to_fill}")

                self.mdt_res.put(step2_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New Step2 Level: {self.step2_res.level}")

            if step3_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"Step3 Level: {self.step3_res.level}")
                    print(f"Putting in {step3_amount_to_fill}")

                self.step3_res.put(step3_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New Step3 Level: {self.step3_res.level}")

            # Wait one unit of simulation time (1 week)
            yield(self.env.timeout(1))

            # increment week number by 1 week
            self.week_number += 1

        # After all weeks processed combine all weekly stats
        self.combined_asst_weekly = pd.concat(self.asst_weekly_stats
                                              ,ignore_index=False)

        self.combined_step2_weekly = pd.concat(self.step2_weekly_stats
                                               ,ignore_index=False)

        self.combined_step3_weekly = pd.concat(self.step3_weekly_stats
                                               ,ignore_index=False)

    ##### generator function that represents the DES generator for referrals
    def generator_patient_referrals(self):

        # get the number of referrals that week based on the mean + seasonal variance
        self.referrals_this_week = round(g.mean_referrals_pw + 
                                    (g.mean_referrals_pw * 
                                    g.referral_rate_lookup.at[
                                    self.week_number+1,'PCVar']))

        print(self.referrals_this_week)
                
        if g.debug_level >= 1:
            print(f'Week {self.week_number}: {self.referrals_this_week}' 
                                                    'referrals generated')
            print('')
            # print(f'Still remaining on triage WL from last week: {g.number_on_triage_wl}')

            # print('')
            # print(f'Still remaining on mdt WL from last week: {g.number_on_mdt_wl}')

            # print('')
            # print(f'Still remaining on Assessment WL from last week: {g.number_on_asst_wl}')
            # print("----------------")

        self.referral_counter = 0

        while self.referral_counter <= self.referrals_this_week:

            # increment the referral counter by 1
            self.referral_counter += 1

            # start up the patient pathway generator
            self.env.process(self.patient_asst_pathway(self.week_number))

        # reset the referral counter
        self.referral_counter = 0

        yield(self.env.timeout(1))


    ###### assessment part of the pathway
    def patient_asst_pathway(self, week_number):

        # decide whether the referral was rejected at screening stage
        self.reject_referral = random.uniform(0,1)
        # decide whether the referral needs to go for review if not rejected
        self.requires_review = random.uniform(0,1)
        # decide whether the referral is rejected at review
        self.review_reject = random.uniform(0,1)
            # decide whether the Patient opts-in
        self.patient_optedin = random.uniform(0,1)
        # decide whether the Patient is accepted following TA
        self.ta_accepted = random.uniform(0,1)
        
        # Increment the patient counter by 1
        self.patient_counter += 1

        # Create a new patient from Patient Class
        p = Patient(self.patient_counter)
        p.week_added = week_number

        # all referrals get screened
        self.asst_results_df.at[p.id, 'Referral Time Screen'
                                        ] = self.random_normal(
                                        g.referral_screen_time
                                        ,g.std_dev)

        # print(f'Week {week_number}: Patient number {p.id} created')

        # check whether the referral was a straight reject or not
        if self.reject_referral <= g.referral_rejection_rate:

            # if this referral is rejected mark as rejected
            self.asst_results_df.at[p.id, 'Run Number'] = self.run_number

            self.asst_results_df.at[p.id, 'Week Number'] = self.week_number

            self.asst_results_df.at[p.id, 'Referral Rejected'] = 1

        else:

            self.asst_results_df.at[p.id, 'Run Number'] = self.run_number

            self.asst_results_df.at[p.id, 'Week Number'] = self.week_number
            # Mark referral as accepted and move on to whether it needs a review
            self.asst_results_df.at[p.id, 'Referral Rejected'] = 0

            # Now decide whether the patient has previously been treated and needs to go for review
            if self.requires_review >= g.referral_review_rate:
                # set flag to show Patient didn't require review
                self.asst_results_df.at[p.id, 'Referral Reviewed'] = 0
                
                self.asst_results_df.at[p.id, 'Review Wait'] = 0

            else:
                # set flag to show Patient required review
                self.asst_results_df.at[p.id, 'Referral Reviewed'] = 1
                # record how long they waited for MDT review between 0 and 2 weeks
                self.asst_results_df.at[p.id, 'Review Wait'] = random.uniform(0,
                                                                g.mdt_freq)

                # decide if they were rejected at Review
                if self.asst_review_reject <= g.review_rej_rate:
                    # set flag to show Patient was rejected at review
                    self.asst_results_df.at[p.id, 'Review Rejected'] = 1
                else:    
                    # otherwise set flag to show they were accepted and go to opt-in
                    self.asst_results_df.at[p.id, 'Review Rejected'] = 0

                    # now decide whether the patient opted-in or not
                    if self.patient_optedin >= g.opt_in_rate:
                        # set flag to show Patient failed to opt-in
                        self.asst_results_df.at[p.id, 'Opted In'] = 0
                        # therefore didn't wait to opt-in
                        self.asst_results_df.at[p.id, 'Opt-in Wait'
                                                    ] = 0
                        self.asst_results_df.at[p.id, 'Opt-in Q Time'
                                                    ] = 0
                    else:    
                        # otherwise set flag to show they opted-in
                        self.asst_results_df.at[p.id, 'Opted In'] = 1
                        # record how long they took to opt-in, 1 week window
                        self.asst_results_df.at[p.id, 'Opt-in Wait'
                                                    ] = random.uniform(0,1)
                        # record lag-time between opting in and TA appointment, max 4 week window
                        self.asst_results_df.at[p.id, 'Opt-in Q Time'
                                                    ] = random.uniform(0,4)
                        
                        # Now do Telephone Assessment
                        # decide if the patient is accepted following TA
                        if self.ta_accepted >= g.ta_accept_rate:
                            # Patient was rejected at TA stage
                            self.asst_results_df.at[p.id, 'TA Outcome'] = 0

                            # used to decide whether further parts of the pathway are run or not
                            self.ta_accepted = 0
                        else:    
                            # Patient was accepted at TA stage
                            self.asst_results_df.at[p.id, 'TA Outcome'] = 1

                                # used to decide whether further parts of the pathway are run or not
                            self.ta_accepted = 1
        print(self.asst_results_df)

        yield self.env.timeout(0)

        #print(f'Patient {p} assessment completed')
        # # replenish resources ready for next week
        # self.triage_res.put(g.triage_resource)
        # self.mdt_res.put(g.mdt_resource)
        # self.asst_res.put(g.asst_resource)

        # reset referral counter ready for next batch
        self.referral_counter = 0

        # Freeze this instance of this function in place for one
        # unit of time i.e. 1 week
        #yield self.env.timeout(1)

        return self.asst_results_df
    
    def calculate_weekly_results(self):
        # Take the mean of the queuing times and the maximum waiting list
        # across patients in this run of the model
 
        self.mean_screen_time = self.asst_results_df['Referral Time Screen'].mean()
        self.reject_ref_total = self.asst_results_df['Referral Rejected'].sum()
        self.mean_optin_wait = self.asst_results_df['Opt-in Wait'].mean()
        self.ref_tot_optin = self.asst_results_df['Opted In'].sum()
        self.mean_qtime_optin = self.asst_results_df['Opt-in Q Time'].mean()
        self.tot_ta_accept = self.asst_results_df['TA Outcome'].sum()

    # This method calculates results over each single run
    def calculate_run_results(self):
        # Take the mean of the queuing times etc.
        self.mean_screen_time = self.asst_results_df['Referral Time Screen'].mean()
        self.reject_ref_total = self.asst_results_df['Referral Rejected'].sum()
        self.mean_optin_wait = self.asst_results_df['Opt-in Wait'].mean()
        self.ref_tot_optin = self.asst_results_df['Opted In'].sum()
        self.mean_qtime_ta =  self.asst_results_df['Opt-in Q Time'].mean()
        self.tot_ta_accept = self.asst_results_df['TA Outcome'].sum()
        # reset waiting lists ready for next run
        # g.number_on_triage_wl = 0
        # g.number_on_mdt_wl = 0
        # g.number_on_asst_wl = 0

    # The run method starts up the DES entity generators, runs the simulation,
    # and in turns calls anything we need to generate results for the run
    def run(self, print_run_results=True):

        # Start up the referral generator to create new referrals
        self.env.process(self.week_runner(g.sim_duration))

        # Run the model for the duration specified in g class
        self.env.run(until=g.sim_duration)

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

        self.asst_weekly_stats = []

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
                my_model.tot_ta_accept,
                ]

            my_model.asst_weekly_stats = pd.DataFrame(my_model.asst_weekly_stats)

            my_model.asst_weekly_stats['Run'] = run

            #print(my_model.asst_weekly_stats)

            self.asst_weekly_dfs.append(my_model.asst_weekly_stats)
                   
        # Once the trial (i.e. all runs) has completed, print the final results
        return self.df_trial_results, pd.concat(self.asst_weekly_dfs)
    
my_trial = Trial()
#pd.set_option('display.max_rows', 1000)
# Call the run_trial method of our Trial class object

df_trial_results, asst_weekly_stats = my_trial.run_trial()

df_trial_results, asst_weekly_stats
        