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
    step2_path_ratios = [0.94,0.06] # Step2 proportion for each route
    step2_pwp_sessions = 6 # number of PwP sessions at Step2
    step2_pwp_1st_mins = 45 # minutes allocated for 1st pwp session
    step2_pwp_fup_mins = 30 # minutes allocated for pwp follow-up session
    step2_session_admin = 15 # number of mins of clinical admin per session
    step2_pwp_period = 16 # max number of weeks PwP delivered over
    step2_group_sessions = 7 # number of group sessions
    step2_group_session_mins = 240 # minutes allocated to pwp group session
    step2_group_dna_rate = 0.216 # Wellbeing Workshop attendance 78.6%

    # Step Moves
    step2_step3_ratio = [0.85,0.15]
    step_routes = ['Step2','Step3']
    step_up_rate = 0.05 # proportion of Step2 that get stepped up
    step_down_rate = 0.003 # proportion of Step3 that get stepped down

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
    ta_resource = number_staff_pwp * 3 # job plan = 3 TA per week per PwP
    pwp_resource = number_staff_pwp * 12 # job plan = 3 x 1st + 9 x FUP per week per PwP
    group_resource = number_staff_pwp * 12 #  job plan = 1 group per week per PwP, assume 12 per group
    cbt_resource = number_staff_cbt * 22 # job plan = 2 x 1st + 20 X FUP per cbt per week
    couns_resource = number_staff_couns * 22 # job plan = 2 x 1st + 20 X FUP per cbt per week

    # Simulation
    sim_duration = 52
    number_of_runs = 10
    std_dev = 3 # used for randomising activity times

    # Result storage
    all_results = []
    weekly_wl_posn = pd.DataFrame() # container to hold w/l position at end of week
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
        self.step2_results_df['IsDropOut'] = [0]
        self.step2_results_df['Caseload'] = [0]

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
        self.step3_results_df['IsDropOut'] = [0]
        self.step3_results_df['Caseload'] = [0]

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

        ######### Create our resources which are appt slots for that week #########
        ########## PwP ##########
        self.ta_res = simpy.Container(
            self.env,capacity=g.ta_resource,
            init=g.ta_resource
            )

        self.pwp_res = simpy.Container(
            self.env,
            capacity=g.pwp_resource,
            init=g.pwp_resource
            )

        self.group_res = simpy.Container(
            self.env,
            capacity=g.group_resource,
            init=g.group_resource
            )
        ########## CBT ##########
        self.cbt_res = simpy.Container(
            self.env,
            capacity=g.cbt_resource,
            init=g.cbt_resource
            )

        ########## Counsellor ##########
        self.couns_res = simpy.Container(
            self.env,
            capacity=g.couns_resource,
            init=g.couns_resource
            )

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

            # weekly waiting list positions
            self.asst_weekly_stats.append(
                {
                 'Week Number':self.week_number,
                 'Referral Screen Mins':self.ref_tot_screen,
                 'Referrals Rejected':self.ref_tot_reject,
                 'Referrals Delay Opt-in':self.ref_optin_delay,
                 'Referrals Opted-in':self.ref_tot_optin,
                 'Referrals Wait Opt-in':self.ref_optin_wait,
                 'TA Total Accept':self.asst_tot_accept
                }
                )

            ######### replenish resources ##########
            ##### PwP #####
            ta_amount_to_fill = g.ta_resource - self.ta_res.level
            pwp_amount_to_fill = g.pwp_resource - self.pwp_res.level
            group_amount_to_fill = g.group_resource - self.group_res.level
            ##### CBT #####
            cbt_amount_to_fill = g.cbt_resource - self.cbt_res.level
            ##### Counsellor #####
            couns_amount_to_fill = g.couns_resource - self.couns_res.level

            ##### PwP #####
            if ta_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"TA Level: {self.ta_res.level}")
                    print(f"Putting in {ta_amount_to_fill}")

                self.ta_res.put(ta_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New TA Level: {self.ta_res.level}")

            if pwp_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"PwP Level: {self.pwp_res.level}")
                    print(f"Putting in {pwp_amount_to_fill}")

                self.pwp_res.put(pwp_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New PwP Level: {self.pwp_res.level}")

            if group_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"Group Level: {self.group_res.level}")
                    print(f"Putting in {group_amount_to_fill}")

                self.group_res.put(group_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New Group Level: {self.group_res.level}")

            ##### CBT #####

            if cbt_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"CBT Level: {self.cbt_res.level}")
                    print(f"Putting in {cbt_amount_to_fill}")

                self.cbt_res.put(cbt_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New CBT Level: {self.cbt_res.level}")

            ##### Counsellor #####

            if couns_amount_to_fill > 0:
                if g.debug_level >= 2:
                    print(f"Couns Level: {self.couns_res.level}")
                    print(f"Putting in {couns_amount_to_fill}")

                self.couns_res.put(couns_amount_to_fill)

                if g.debug_level >= 2:
                    print(f"New Couns Level: {self.couns_res.level}")

            # Wait one unit of simulation time (1 week)
            yield(self.env.timeout(1))

            # increment week number by 1 week
            self.week_number += 1

    ##### generator function that represents the DES generator for referrals
    def generator_patient_referrals(self):

        # get the number of referrals that week based on the mean + seasonal variance
        self.referrals_this_week = round(g.mean_referrals_pw +
                                    (g.mean_referrals_pw *
                                    g.referral_rate_lookup.at[
                                    self.week_number+1,'PCVar'])) # weeks start at 1

        print(self.referrals_this_week)

        print(self.referrals_this_week)

        if g.debug_level >= 1:
            print(f'Week {self.week_number}: {self.referrals_this_week}'
                                                    'referrals generated')
            print('')
            # print(f'Still remaining on TA WL from last week: {g.number_on_ta_wl}')

            # print('')
            # print(f'Still remaining on PwP WL from last week: {g.number_on_pwp_wl}')

            # print('')
            # print(f'Still remaining on Group WL from last week: {g.number_on_group_wl}')

            # print('')
            # print(f'Still remaining on CBT WL from last week: {g.number_on_cbt_wl}')

            # print('')
            # print(f'Still remaining on Couns WL from last week: {g.number_on_couns_wl}')
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

    ###### assessment part of the pathway #####
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
                        self.asst_results_df.at[p.id, 'Opt-in Wait'] = 0
                        # and didn't queue for TA appt
                        self.asst_results_df.at[p.id, 'Opt-in Q Time'] = 0
                    else:
                        # otherwise set flag to show they opted-in
                        self.asst_results_df.at[p.id, 'Opted In'] = 1
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

                            # used to decide whether further parts of the pathway are run or not
                            self.ta_accepted = 0
                        else:
                            # Patient was accepted at TA stage
                            self.asst_results_df.at[p.id, 'TA Outcome'] = 1

                                # used to decide whether further parts of the pathway are run or not
                            self.ta_accepted = 1

        # decide which pathway the patient has been allocated to
        # Select 2 options based on the given probabilities
        self.step_options = random.choices(g.step_routes, weights=g.step2_step3_ratio, k=50)

        #print(self.selected_step)
        self.selected_step = random.choice(self.step_options)

        print(self.selected_step)

        self.asst_results_df.at[p.id, 'Treatment Path'] = self.selected_step

        # print(self.asst_results_df)

        # reset referral counter ready for next batch
        self.referral_counter = 0

        self.env.process(self.pathway_runner(p.id))

        yield self.env.timeout(0)

        return self.asst_results_df

    def pathway_runner(self, patient):

        p = patient

        print(f'Patient {p.id} sent down {self.selected_step} pathway')

        if self.selected_step == 'Step2':
            self.env.process(self.patient_step2_pathway(p))
        else:
            self.env.process(self.patient_step3_pathway(p))

    ###### step2 pathway #####
    def patient_step2_pathway(self, patient):

        p = patient
        # Select one of 2 treatment options based on the given probabilities
        self.step2_pathway_options = random.choices(g.step2_routes,
                                                weights=g.step2_path_ratios,
                                                k=self.referrals_this_week)

        self.selected_step2_pathway = random.choice(self.step2_pathway_options)

        self.step2_results_df.at[p.id, 'Step2 Route'
                                            ] = self.selected_step2_pathway

        # push the patient down the chosen step2 route
        if self.selected_step2_pathway == 'PWP':
            self.env.process(self.step2_pwp_process(p))
        else:
            self.env.process(self.step2_group_process(p))

     ###### step2 pathway #####
    def patient_step3_pathway(self, patient):

        p = patient
        # Select one of 2 treatment options based on the given probabilities
        self.step3_pathway_options = random.choices(g.step3_routes,
                                                weights=g.step3_path_ratios,
                                                k=self.referrals_this_week)

        self.selected_step3_pathway = random.choice(self.step3_pathway_options)

        self.step3_results_df.at[p.id, 'Step3 Route'
                                            ] = self.selected_step3_pathway

        # push the patient down the chosen step2 route
        if self.selected_step3_pathway == 'CBT':
            self.env.process(self.step3_cbt_process(p))
        else:
            self.env.process(self.step3_couns_process(p))

    def step2_pwp_process(self,patient):

        p = patient

        # counter for number of group sessions
        self.pwp_session_counter = 0
        # counter for applying DNA policy
        self.pwp_dna_counter = 0

        g.number_on_pwp_wl += 1

        start_q_pwp = self.env.now

        # Record where the patient is on the TA WL
        self.step2_results_df.at[p.id, 'PwP WL Posn'] = \
                                            g.number_on_pwp_wl

        # Request a PwP resource from the container
        with self.pwp_res.get(1) as pwp_req:
            yield pwp_req

        # add to caseload
        g.number_on_pwp_cl +=1

        # print(f'Patient {p} started PwP')

        # as each patient reaches this stage take them off PwP wl
        g.number_on_pwp_wl -= 1

        if g.debug_level >= 2:
            print(f'Week {self.env.now}: Patient number {p.id} (added week {p.week_added}) put through PwP')

        end_q_pwp = self.env.now

        # Calculate how long patient queued for TA
        self.q_time_pwp = end_q_pwp - start_q_pwp
        # Record how long patient queued for TA
        self.asst_results_df.at[p.id, 'PwP Q Time'] = self.q_time_pwp

        while self.pwp_session_counter <= g.step2_pwp_sessions:

            # increment the pwp session counter by 1
            self.pwp_session_counter += 1

            # record the pwp session number for the patient
            self.step2_results_df.at[p.id, 'Session Number'] = self.pwp_session_counter

            # keep going for all number sessions or until patient DNA's twice
            while self.pwp_dna_counter < 2:

                # record stats for the patient against this session number
                self.step2_results_df.at[p.id,'Patient ID'] = p
                self.step2_results_df.at[p.id,'Week Number'] = self.week_number
                self.step2_results_df.at[p.id,'Run Number'] = self.run_number
                self.step2_results_df.at[p.id, 'Treatment Route'
                                                    ] = self.selected_step2_pathway

                # decide whether the session was DNA'd
                self.dna_pwp_session = random.uniform(0,1)

                if self.dna_pwp_session <= g.step2_pwp_dna_rate:
                    self.step2_results_df.at[p.id, 'IsDNA'] = 1
                    self.pwp_dna_counter += 1
                    # if session is DNA just record admin mins as clinical time will be used elsewhere
                    self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin
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
        else:
            self.step2_results_df.at[p.id, 'IsDropOut'] = 0

        # remove from Step 2 Caseload as have either completed treatment or dropped out
        self.step2_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for pwp sessions
        self.pwp_session_counter = 0
        self.pwp_dna_counter = 0

        # remove from caseload
        g.number_on_pwp_cl -=1

        yield self.env.timeout(0)

    def step2_group_process(self,patient):

        p = patient

        # counter for number of group sessions
        self.group_session_counter = 0
        # counter for applying DNA policy
        self.group_dna_counter = 0

        g.number_on_group_wl += 1

        start_q_group = self.env.now

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
            print(f'Week {self.env.now}: Patient number {p.id} (added week {p.week_added}) put through Groups')

        end_q_group = self.env.now

        # Calculate how long patient queued for groups
        self.q_time_group = end_q_group - start_q_group
        # Record how long patient queued for groups
        self.asst_results_df.at[p.id, 'Group Q Time'] = self.q_time_group

        while self.group_session_counter <= g.step2_group_sessions:

            # increment the group session counter by 1
            self.group_session_counter += 1

            # record the session number for the patient
            self.step2_results_df.at[p.id, 'Session Number'] = self.group_session_counter
            # mark patient as still on Step2 Caseload
            self.step2_results_df.at[p.id, 'Caseload'] = 1

            # keep going for all number sessions or until patient DNA's twice
            while self.group_dna_counter < 2:

                # record stats for the patient against this session number
                self.step2_results_df.at[p.id,'Patient ID'] = p
                self.step2_results_df.at[p.id,'Week Number'] = self.week_number
                self.step2_results_df.at[p.id,'Run Number'] = self.run_number
                self.step2_results_df.at[p.id, 'Treatment Route'
                                                    ] = self.selected_step2_pathway

                # decide whether the session was DNA'd
                self.dna_group_session = random.uniform(0,1)

                if self.dna_group_session <= g.step2_group_dna_rate:
                    self.step2_results_df.at[p.id, 'IsDNA'] = 1
                    self.group_dna_counter += 1
                    self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin
                else:
                    self.step2_results_df.at[p.id, 'IsDNA'] = 0
                    self.step2_results_df.at[p.id,'Session Time'] = g.step2_group_session_mins
                    self.step2_results_df.at[p.id,'Admin Time'] = g.step2_session_admin

        # record whether patient dropped out before completing Wellbeing Workshop
        if self.group_dna_counter >= 2:
            self.step2_results_df.at[p.id, 'IsDropOut'] = 1
        else:
            self.step2_results_df.at[p.id, 'IsDropOut'] = 0
        # remove from Step 2 Caseload as have either completed treatment or dropped out
        self.step2_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for group sessions
        self.group_session_counter = 0
        self.group_dna_counter = 0

        # remove from caseload
        g.number_on_group_cl -=1

        yield self.env.timeout(0)

    def step3_cbt_process(self,patient):

        p = patient

        # counter for number of cbt sessions
        self.cbt_session_counter = 0
        # counter for applying DNA policy
        self.cbt_dna_counter = 0

        g.number_on_cbt_wl += 1

        start_q_cbt = self.env.now

        # Record where the patient is on the cbt WL
        self.step3_results_df.at[p.id, 'CBT WL Posn'] = \
                                            g.number_on_cbt_wl

        # Request a cbt resource from the container
        with self.cbt_res.get(1) as cbt_req:
            yield cbt_req

        # add to caseload
        g.number_on_cbt_cl +=1

        # print(f'Patient {p} started CBT')

        # as each patient reaches this stage take them off CBT wl
        g.number_on_cbt_wl -= 1

        if g.debug_level >= 2:
            print(f'Week {self.env.now}: Patient number {p.id} (added week {p.week_added}) put through CBT')

        end_q_cbt = self.env.now

        # Calculate how long patient queued for CBT
        self.q_time_cbt = end_q_cbt - start_q_cbt
        # Record how long patient queued for CBT
        self.asst_results_df.at[p.id, 'CBT Q Time'] = self.q_time_cbt

        while self.cbt_session_counter <= g.step3_cbt_sessions:

            # increment the cbt session counter by 1
            self.cbt_session_counter += 1

            # record the cbt session number for the patient
            self.step3_results_df.at[p.id, 'Session Number'] = self.cbt_session_counter

            # keep going for all number sessions or until patient DNA's twice
            while self.cbt_dna_counter < 2:

                # record stats for the patient against this session number
                self.step3_results_df.at[p.id,'Patient ID'] = p
                self.step3_results_df.at[p.id,'Week Number'] = self.week_number
                self.step3_results_df.at[p.id,'Run Number'] = self.run_number
                self.step3_results_df.at[p.id, 'Treatment Route'
                                                    ] = self.selected_step3_pathway

                # decide whether the session was DNA'd
                self.dna_cbt_session = random.uniform(0,1)

                if self.dna_cbt_session <= g.step3_cbt_dna_rate:
                    self.step3_results_df.at[p.id, 'IsDNA'] = 1
                    self.cbt_dna_counter += 1
                    # if session is DNA just record admin mins as clinical time will be used elsewhere
                    self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin
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
        else:
            self.step3_results_df.at[p.id, 'IsDropOut'] = 0

        # remove from Step 3 Caseload as have either completed treatment or dropped out
        self.step3_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for cbt sessions
        self.cbt_session_counter = 0
        self.cbt_dna_counter = 0

        # remove from caseload
        g.number_on_cbt_cl -=1

        yield self.env.timeout(0)

    def step3_couns_process(self,patient):

        p = patient

        # counter for number of couns sessions
        self.couns_session_counter = 0
        # counter for applying DNA policy
        self.couns_dna_counter = 0

        g.number_on_couns_wl += 1

        start_q_couns = self.env.now

        # Record where the patient is on the TA WL
        self.step3_results_df.at[p.id, 'Couns WL Posn'] = \
                                            g.number_on_couns_wl

        # Request a Couns resource from the container
        with self.couns_res.get(1) as couns_req:
            yield couns_req

        # add to caseload
        g.number_on_couns_cl +=1

        # print(f'Patient {p} started Couns')

        # as each patient reaches this stage take them off PwP wl
        g.number_on_couns_wl -= 1

        if g.debug_level >= 2:
            print(f'Week {self.env.now}: Patient number {p.id} (added week {p.week_added}) put through Couns')

        end_q_couns = self.env.now

        # Calculate how long patient queued for TA
        self.q_time_couns = end_q_couns - start_q_couns
        # Record how long patient queued for TA
        self.asst_results_df.at[p.id, 'Couns Q Time'] = self.q_time_couns

        while self.couns_session_counter <= g.step3_couns_sessions:

            # increment the group session counter by 1
            self.couns_session_counter += 1

            # record the session number for the patient
            self.step3_results_df.at[p.id, 'Session Number'] = self.couns_session_counter
            # mark patient as still on Step2 Caseload
            self.step3_results_df.at[p.id, 'Caseload'] = 1

            # keep going for all number sessions or until patient DNA's twice
            while self.couns_dna_counter < 2:

                # record stats for the patient against this session number
                self.step3_results_df.at[p.id,'Patient ID'] = p
                self.step3_results_df.at[p.id,'Week Number'] = self.week_number
                self.step3_results_df.at[p.id,'Run Number'] = self.run_number
                self.step3_results_df.at[p.id, 'Treatment Route'
                                                    ] = self.selected_step3_pathway

                # decide whether the session was DNA'd
                self.dna_couns_session = random.uniform(0,1)

                if self.dna_couns_session <= g.step3_couns_dna_rate:
                    self.step3_results_df.at[p.id, 'IsDNA'] = 1
                    self.couns_dna_counter += 1
                    # if session is DNA just record admin mins as clinical time will be used elsewhere
                    self.step3_results_df.at[p.id,'Admin Time'] = g.step3_session_admin
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
        else:
            self.step3_results_df.at[p.id, 'IsDropOut'] = 0
        # remove from Step 2 Caseload as have either completed treatment or dropped out
        self.step3_results_df.at[p.id, 'Caseload'] = 0

        # reset counters for couns sessions
        self.couns_session_counter = 0
        self.couns_dna_counter = 0

        # add to caseload
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

        self.asst_weekly_dfs = []

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
            # add the run number to the dataframe
            my_model.asst_weekly_stats['Run'] = run

            #print(my_model.asst_weekly_stats)
            # append stats for that week to asst dataframe
            self.asst_weekly_dfs.append(my_model.asst_weekly_stats)

        # Once the trial (i.e. all runs) has completed, print the final results and combine all the weekly dataframes
        return self.df_trial_results, pd.concat(self.asst_weekly_dfs)

if __name__ == "__main__":
    my_trial = Trial()
    #pd.set_option('display.max_rows', 1000)
    # Call the run_trial method of our Trial class object

    df_trial_results, asst_weekly_dfs = my_trial.run_trial()

    df_trial_results, asst_weekly_dfs
