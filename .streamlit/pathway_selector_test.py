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
    step2_routes = ['PwP','Groups'] # possible Step2 routes
    step2_path_ratios = [0.368,0.632] # Step2 proportion for each route
    step2_pwp_sessions = 6 # number of PwP sessions at Step2
    step2_pwp_period = 16 # max number of weeks PwP delivered over
    step2_group_range = [6,12] # range of possible group sessions
    step2_asst_admin = 15 # number of mins of clinical admin per session


    # Step Moves
    step2_step3_ratio = [0.85,0.15]
    step_routes = ['Step2','Step3']
    step_up_rate = 0.05 # proportion of Step2 that get stepped up
    step_down_rate = 0.003 # proportion of Step3 that get stepped down

    # Step 3
    step3_ratio = 0.15 # proportion of patients that go onto Step3 vs Step2
    step3_routes = ['CBT','DepC'] # possible Step routes
    step3_path_ratios = [0.368,0.632] # Step3 proportion for each route ##### Need to clarify exact split

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


# Define the array and the corresponding probabilities
# Select 2 options based on the given probabilities
selected_step = random.choices(g.step_routes, weights=g.step2_step3_ratio, k=50)

selected_path = random.choice(selected_step)

print(selected_step)

print(selected_path)

# Select 2 options based on the given probabilities
selected_step2_pathway = random.choices(g.step2_routes, weights=g.step2_path_ratios, k=50)

print(selected_step2_pathway)

# Select 2 options based on the given probabilities
selected_step3_pathway = random.choices(g.step3_routes, weights=g.step3_path_ratios, k=50)

print(selected_step3_pathway)