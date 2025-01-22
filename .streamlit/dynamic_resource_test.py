import simpy

number_staff_pwp = 10
number_staff_cbt = 9
number_staff_couns = 10
number_staff_pwp = 10
step2_pwp_sessions = 6 # number of PwP sessions at Step2
debug_level = 1
pwp_caseload = 30
pwp_id_counter = 0 # starting ID for PwP resources
group_resource = number_staff_pwp #  job plan = 1 group per week per PwP, assume 12 per group
group_id_counter = 0 # starting ID for Group resources
cbt_resource = number_staff_cbt # job plan = 2 x 1st + 20 X FUP per cbt per week
cbt_caseload = 25
cbt_id_counter = 0 # starting ID for CBT resources
couns_resource = number_staff_couns # job plan = 2 x 1st + 20 X FUP per cbt per week
couns_caseload = 25
couns_id_counter = 0 # starting ID for Couns resources

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

env = simpy.Environment()

r_type = 'PwP'

r_id = 0 # don't reset this, allow it to conitunally increment so no duplicate resources

pwp_resources = {f'{r_type}_{i}':simpy.Container(env,
                    capacity=step2_pwp_sessions,
                    init=step2_pwp_sessions) for i in range(number_staff_pwp)}
        
        # resource_id = f'{r_type}_{i}'
        
        # resources[resource_id] = simpy.Container(env,
        #             capacity=step2_pwp_sessions,
        #             init=step2_pwp_sessions
        #     )
        
        # r_id +=1}

# if debug_level == 1:
#                 #print(resources[f'{r_type}_{r_id}'].capacity)
#                 print(resources[f'{r_type}_{i}'].capacity)

def find_caseload_slot(res_dictionary):
        for resource_id, resource_value in res_dictionary.items():
            if resource_value.level > 10:
                return resource_id, resource_value
        return None, None
            
find_caseload_slot(pwp_resources)

# if resources are available create resource at start of pathway route
# otherwise wait unti a resource is available
# create a counter to determine how many staff are left. if this is > 0 allow a
# resource to be created otherwise wait until a resource becomes available


number_staff_pwp = 10
number_staff_cbt = 9.0
number_staff_couns = 10
step2_pwp_sessions = 6 # number of PwP sessions at Step2
debug_level = 1
pwp_caseload = 30
pwp_id = 0 # unique ID for PwP resources
group_resource = number_staff_pwp #  job plan = 1 group per week per PwP, assume 12 per group
group_id = 0 # starting ID for Group resources
cbt_resource = number_staff_cbt # job plan = 2 x 1st + 20 X FUP per cbt per week
cbt_caseload = 25
cbt_id_counter = 0 # starting ID for CBT resources
couns_resource = number_staff_couns # job plan = 2 x 1st + 20 X FUP per cbt per week
couns_caseload = 25
couns_id_counter = 0 # starting ID for Couns resources

r_type = 1
class Model:
    # this function builds a caseload variable to record availability on the caseload  
    def caseload_counter_builder(self,r_type,r_id):

        self.caseload = []

        if r_type == '1':
            # caseload counter for PwP
            self.caseload[f'{r_type}_{r_id}'] = pwp_caseload

        elif r_type == '2':
            # caseload counter for CBT
            self.caseload[f'{r_type}_{r_id}'] = cbt_caseload

        if r_type == '3':
            # caseload counter for Couns
            self.caseload[f'{r_type}_{r_id}'] = couns_caseload
            #if debug_level >=1:
    # this function builds a staff resource if a staff member is available
    def resource_builder(self,r_type,r_id):

        self.resource = {}
        
        self.resource_id = f'{r_type}_{r_id}'

        if r_type == '1':
            self.resource[self.resource_id] = simpy.Container(env,
                        capacity=step2_pwp_sessions,
                        init=step2_pwp_sessions)
            
        elif r_type == '2':
            self.resource[self.resource_id] = simpy.Container(env,
                        capacity=step3_cbt_sessions,
                        init=step3_cbt_sessions)
        elif r_type == '3':
            self.resource[self.resource_id] = simpy.Container(env,
                        capacity=step3_couns_sessions,
                        init=step3_couns_sessions)

        # create a caseload counter for this resource
        self.env.process(self.caseload_builder(r_type,r_id))
