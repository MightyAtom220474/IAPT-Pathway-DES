import simpy

number_staff_pwp = 10
step2_pwp_sessions = 6 # number of PwP sessions at Step2
debug_level = 1

env = simpy.Environment()

r_type = 'PwP'

resources = {}

r_id = 0 # don't reset this, allow it to conitunally increment so no duplicate resources

for i in range(number_staff_pwp):
        
        resource_id = f'{r_type}_{r_id}'
        
        resources[resource_id] = simpy.Container(env,
                    capacity=step2_pwp_sessions,
                    init=step2_pwp_sessions
            )
        
        r_id +=1

if debug_level == 1:
                #print(resources[f'{r_type}_{r_id}'].capacity)
                print(resources)

# if resources are available create resource at start of pathway route
# otherwise wait unti a resource is available
# create a counter to determine how many staff are left. if this is > 0 allow a
# resource to be created otherwise wait until a resource becomes available

def resource_builder(r_type,r_id):
    
    resource_id = f'{r_type}_{r_id}'
        
    resource_id = simpy.Container(env,
                capacity=step2_pwp_sessions,
                init=step2_pwp_sessions)

