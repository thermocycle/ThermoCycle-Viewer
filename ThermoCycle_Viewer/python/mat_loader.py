from buildingspy.io.outputfile import Reader
import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate
import copy
import CoolProp
import CoolProp.CoolProp as CP
import subprocess

class struct(object): pass
    
def find_matches(l,s):
    """ Find elements in a list of strings where an entry in the list contains the given substring """
    return [el for el in l if el.find(s) > -1]

def find_T_profiles(filename, Ninterp):
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
    
    # Make a deepcopy to make sure the data gets copied, and not just the pointers
    processed = copy.deepcopy(raw)
    
    # The old irregularly spaced time data
    time_old = raw['time']
    
    # Interpolated time data
    time_interp = np.linspace(min(time_old), max(time_old), Ninterp)
    
    # Now interpolate all the data onto regularly spaced grid in time
    for profile in processed.keys():
        if profile == 'time': continue #skip 'time', not a profile
            
        # Interpolate onto the gridded times, and save the data back to 
        # processed
        for i,el in enumerate(processed[profile]):
            el_new = scipy.interpolate.interp1d(time_old, el)(time_interp)
            
            processed[profile][i] = el_new
    
    # Save the gridded time into processed
    processed['time'] = time_interp
    
    return raw, processed
    
def find_states(filename, Ninterp):
    
    def guess_fluid(key):
        time, T = r.values(key + '.T')
        time, rho = r.values(key + '.d')
        time, p = r.values(key + '.p')
        p /= 1000
        
        ps = []
        for fluid in CoolProp.__fluids__:
            if T[0] < CP.Props(fluid, 'Tmin'): continue
            ps.append(CP.Props('P','T',float(T[0]),'D',float(rho[0]),fluid))
        
        diffs = np.abs(np.array(ps) - p[0])
        
        diffs, fluids = zip(*sorted(zip(diffs,CoolProp.__fluids__)))
        
        return fluids[0], diffs[0]
        
    r = Reader(filename, "dymola")

    # Names of all the variables in the file
    names = r.varNames()
    
    # Get things that have .h, .T, and .s
    has_T = [name.rsplit('.',1)[0] for name in names if name.endswith('.T')]
    has_d = [name.rsplit('.',1)[0] for name in names if name.endswith('.d')]
    has_h = [name.rsplit('.',1)[0] for name in names if name.endswith('.h')]
    has_s = [name.rsplit('.',1)[0] for name in names if name.endswith('.s')]

    # Take the intersection of all these lists
    keys = list(set(has_T).intersection(has_h).intersection(has_s).intersection(has_d))
    
    # Start with empty dictionary for the states
    raw = {}
    
    for key in keys:
        
        s = struct()
        
        # Get the fluid for this state
        s.fluid, s.fluid_diff = guess_fluid(key)
        
        for attr in find_matches(names, key):
            time, val = r.values(attr)
            setattr(s, attr.rsplit('.',1)[1], val)
            
            if 'time' not in raw:
                raw['time'] = time
                
        # Store in the dictionary
        raw[key] = s
    
    # Interpolate the data
    processed = copy.deepcopy(raw)
    
    # The old irregularly spaced time data
    time_old = raw['time']
    
    # Interpolated time data
    time_interp = np.linspace(min(time_old), max(time_old), Ninterp)
    
    # Now interpolate all the data onto regularly spaced grid in time
    for state in processed.keys():
        if state == 'time': continue #skip 'time', not a profile
            
        # Interpolate onto the gridded times, and save the data back to 
        # processed
        for k,val in processed[state].__dict__.iteritems():
            if k in ['fluid', 'fluid_diff']: continue
            val_new = scipy.interpolate.interp1d(time_old, val)(time_interp)
            setattr(processed[state], k, val_new)
    
    # Save the gridded time into processed
    processed['time'] = time_interp
    
    return raw, processed
            
def plot_Tprofile_at_step(i, processed, fname = None, ax = None):
    """
    Plot each of the profiles at this given time step index of the interpolated data
    """
    
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
    for profile in sorted(processed.keys()):
        if profile == 'time': continue
        
        vals =  [el[i] for el in processed[profile]]
            
        ax.plot(range(len(vals)),vals, 'o-', label = profile)
        
    ax.legend(loc = 'best')
    
    if fname is not None:
        plt.savefig(fname, dpi = 100)
        
def plot_Ts_at_step(i, processed, fname = None, ax = None):
    """
    Plot each of the profiles at this given time step index of the interpolated data
    """
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
    p, h, T, rho, s, fluids = [], [], [], [], [], []
    for k, state in processed.iteritems():
        if k == 'time': continue
        p.append(state.p[i])
        h.append(state.h[i])
        T.append(state.T[i])
        rho.append(state.d[i])
        s.append(state.s[i])
        fluids.append(state.fluid)
            
    if len(set(fluids)) == 1: # all fluids are the same
        Tsat = np.linspace(CP.Props(fluids[0],'Tmin')+1e-5, CP.Props(fluids[0],'Tcrit')-0.1,200)
        ssatV = CP.PropsSI('S','T',Tsat,'Q',1,fluids[0])
        ssatL = CP.PropsSI('S','T',Tsat,'Q',0,fluids[0])
        ax.plot(ssatV,Tsat,'k')
        ax.plot(ssatL,Tsat,'k')
        
    ax.plot(s, T, 'o')
    
    if fname is not None:
        plt.savefig(fname, dpi = 100)
    
if __name__=='__main__':
    raw_T_profile, processed_T_profile = find_T_profiles("SQThesisModel.mat", 200)
    raw_states, processed_states = find_states("SQThesisModel.mat", 200)
    
    for i in range(200):
        plot_Ts_at_step(i, processed_states, 'States{s:05d}.png'.format(s = i))
        plt.close()
    subprocess.call('convert States*.png StatesAnimation.gif', shell = True)
    subprocess.call('erase States*.png', shell = True)
        
    for i in range(200):
        plot_Tprofile_at_step(i, processed_T_profile, 'Tprofile{s:05d}.png'.format(s = i))
        plt.close()
    subprocess.call('convert Tprofile*.png TprofileAnimation.gif', shell = True)
    subprocess.call('erase Tprofile*.png', shell = True)