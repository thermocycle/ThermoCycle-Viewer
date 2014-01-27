from buildingspy.io.outputfile import Reader
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate
import copy

def find_matches(l,s):
    """ Find elements in a list of strings where an entry in the list contains the given substring """
    return [el for el in l if el.find(s) > -1]

def read_and_interpolate(filename, Ninterp):
    r = Reader(filename, "dymola")

    # Names of all the variables in the file
    names = r.varNames()

    # Find names that have a T_profile in them
    T_profile_names = find_matches(names, 'T_profile')

    raw = {}

    # More post-processing on T_profile names
    for name in T_profile_names:
        if name.endswith('T_profile.n'):
            
            # How many entries we should find in the lists
            (time, N) = r.values(name)
            
            # N comes out as a 2 element array with the floating point value in both cells
            N = int(N[0]) 
            
            # Get the root name for the profile, something like 'Condenser.Summary.T_profile'
            root_name = name.strip('.n')
            
            # Find entries that match the root name
            root_matches = find_matches(T_profile_names,root_name)
            
            # Loop over the number of elements in the profile
            for i in range(1, N+1):
                
                # Entries that have an entry containing the index - like [1]
                for element in find_matches(root_matches, '['+str(i)+']'):
                    
                    # Get the root name - something like 'Evaporator.Summary.T_profile.Twall'
                    element_root_name = element.split('[')[0]
                    
                    # Get the actual value
                    (time, vals) = r.values(element)
                    
                    if element_root_name in raw:
                        raw[element_root_name].append(vals)
                    else:
                        raw[element_root_name] = [vals]
                        
                    # Store the time in the dictionary too
                    if 'time' not in raw:
                        raw['time'] = time
    
    # Make a deepcopy to make sure the data gets copied, and not just the locations of the pointers
    processed = copy.deepcopy(raw)
    
    # The old irregularly spaced time data
    time_old = raw['time']
    
    # Interpolated time data
    time_interp = np.linspace(min(time_old), max(time_old), Ninterp)
    
    # Now interpolate all the data onto regularly spaced grid in time
    for profile in processed.keys():
        if profile == 'time': continue #skip 'time', not a profile
            
        for i,el in enumerate(processed[profile]):
            el_new = scipy.interpolate.interp1d(time_old, el)(time_interp)
            
            processed[profile][i] = el_new
    
    processed['time'] = time_interp
    
    return raw, processed

def plot_at_step(i, processed, fname = None):
    """
    Plot each of the profiles at this given time step index of the interpolated data
    """
    for profile in sorted(processed.keys()):
        if profile == 'time': continue
        
        vals =  [el[i] for el in processed[profile]]
            
        plt.plot(range(len(vals)),vals, 'o-', label = profile)
        
    plt.legend(loc = 'best')
    
    if fname is None:
        plt.show()
        plt.close('all')
    else:
        plt.savefig(fname, dpi = 100)
        plt.close()
        
raw, processed = read_and_interpolate("SQThesisModel.mat", 200)

for i in range(200):
    plot_at_step(i, processed, '{s:04d}.png'.format(s = i))
