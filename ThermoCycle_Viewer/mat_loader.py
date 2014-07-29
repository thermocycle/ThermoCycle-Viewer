from __future__ import print_function

import numpy as np
import matplotlib.pyplot as plt
import scipy.interpolate
import copy
import CoolProp
import CoolProp.CoolProp as CP
import subprocess
import scipy.io

class Reader(object):
    
    def __init__(self, filename, dummy_string):
        mat_data = scipy.io.loadmat(filename)
        
        names_shape = mat_data['data_1'].shape
        
        Nelements = max(mat_data['dataInfo'].shape)
        assert(Nelements > min(mat_data['dataInfo'].shape))
        
        nr, nc = mat_data['dataInfo'].shape
        
        # Transpose the data so that the first index is the item of interest
        if nr > nc:
            names = mat_data['name'] # Don't touch
            data_1 = mat_data['data_1'].T
            data_2 = mat_data['data_2'].T
            dataInfo = mat_data['dataInfo']
        else:
            # Split up each string
            list_of_lists = [[_ for _ in row] for row in mat_data['name']]
            
            # Put them all into a matrix, transpose it
            transposed = np.array(list_of_lists).T
            
            # Split back up into list of strings; add a '\x00' to each one to split properly later on
            names = [''.join(t.tolist()).strip()+'\x00' for t in transposed]
            data_1 = mat_data['data_1']
            data_2 = mat_data['data_2']
            dataInfo = mat_data['dataInfo'].T
        
        data = {}
        data['time'] = data_2[0,:]
        for i in range(Nelements):
            element_name = ''.join(str(names[i]))
            
            # One row looks like 1, 2, 0, -1 - indexes are 1-based
            data_index, index = dataInfo[i, 0:2]
            
            # Make the index 0-based
            index -= 1
            
            if index < 0: continue
            
            if data_index == 1:
                values = np.ones_like(data['time'])*data_1[index,0]
            else:
                values = data_2[index,:]
                
            # Remove the \x00
            element_name = element_name.encode('ascii').split('\x00',1)[0]
                
            data[element_name] = values
            
        self.data = data
        
    def varNames(self):
        return self.data.keys()
        
    def values(self, key):
        return self.data['time'], self.data[key]

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
    
    # No temperature profiles
    if not T_profile_names:
        return None,None,None,None

    raw = {}
    has_xaxis = False

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
            root_matches = find_matches(T_profile_names, root_name)
            
            Xaxis = []
            
            # ------------------------------
            # Extract the Xaxis if it has it
            # ------------------------------
            for i in range(1, N+1):
                    
                # Get the root name - something like 'Evaporator.Summary.T_profile.Twall'
                xaxis_name = root_name + '.Xaxis[' + str(i) + ']'
                
                if xaxis_name in root_matches:
                    
                    # Get the actual value
                    (time, vals) = r.values(xaxis_name)
                    
                    # Append to the list
                    Xaxis.append(vals)
                    
                    # Remove key so it doesn't end up in the temperature profiles
                    root_matches.remove(xaxis_name)
                    
            if Xaxis:
                has_xaxis = True
            
            # Loop over the number of elements in the profile
            for i in range(1, N+1):
                
                # Entries that have an entry containing the index - like [1]
                for element in find_matches(root_matches, '['+str(i)+']'):
                    
                    # Get the root name - something like 'Evaporator.Summary.T_profile.Twall'
                    element_root_name = element.split('[')[0]
                    
                    # Get the actual value
                    (time, vals) = r.values(element)

                    # If constant and zero, fill with NAN so it won't plot
                    if (np.max(vals) - np.min(vals)) < 1e-10 and np.max(vals) < 1e-10:
                        vals[:] = np.nan

                    if element_root_name in raw:
                        raw[element_root_name].append(vals)
                    else:
                        raw[element_root_name] = [vals]
                        
                    # Store the time in the dictionary too
                    if 'time' not in raw:
                        raw['time'] = time
    
    max_Tprofile = {}
    min_Tprofile = {}
    
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
        for i, el in enumerate(processed[profile]):
            
            el_new = scipy.interpolate.interp1d(time_old, el)(time_interp)
            
            processed[profile][i] = el_new
    
    processed['limits'] = dict(Tmin = min_Tprofile, Tmax = max_Tprofile)
    
    # Interpolate onto the gridded times, and save the data back to processed
    if has_xaxis:
        for i, el in enumerate(Xaxis):
            if time_old.shape != el.shape:
                if el.shape == (2,) and el[0] == el[1]:
                    el = el[0]*np.ones_like(time_old)
                elif time_old.shape == (2,):
                    print('reshaping', time_old)
                    time_old = np.linspace(time_old[0], time_old[1], el.size)
                else:
                    print(time_old.shape, el.shape)
            
            Xaxis[i] = scipy.interpolate.interp1d(time_old, el)(time_interp)
        
        processed['Xaxis'] = Xaxis
    
    # Save the gridded time into processed
    processed['time'] = time_interp
    
    return raw, processed
    
def find_states(filename, Ninterp):
    
    def guess_fluid(key):
        time, T = r.values(key + '.T')
        time, rho = r.values(key + '.d')
        time, p = r.values(key + '.p')
        
        ps = []
        for fluid in CoolProp.__fluids__:
            if T[0] < CP.Props(fluid, 'Tmin'): continue
            try:
                ps.append(CP.PropsSI('P','T',float(T[0]),'D',float(rho[0]),fluid))
            except ValueError:
                ps.append(1e99)
        
        diffs = np.abs((np.array(ps) - p[0])/p[0])
        
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
    
    # No temperature profiles
    if not keys:
        return None,None
    
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
            if time_old.shape != val.shape and val.shape == (2,) and val[0] == val[1]:
                val = val[0]*np.ones_like(time_old)
                
            val_new = scipy.interpolate.interp1d(time_old, val)(time_interp)
            setattr(processed[state], k, val_new)
    
    # Save the gridded time into processed
    processed['time'] = time_interp
    
    # Post-process the processed states and put them into a list of dictionaries of lists
    states = []
    all_fluids = []
    limits = {}
    for i in range(len(time_interp)):
        p, h, T, rho, s, fluids = [], [], [], [], [], []
        for k, state in processed.iteritems():
            if k == 'time': continue
            p.append(state.p[i])
            h.append(state.h[i])
            T.append(state.T[i])
            rho.append(state.d[i])
            s.append(state.s[i])
            fluids.append(state.fluid)
            
            if 'pmax' not in limits or state.p[i] > limits['pmax']:
                limits['pmax'] = state.p[i]
            if 'pmin' not in limits or state.p[i] < limits['pmin']:
                limits['pmin'] = state.p[i]
            if 'Tmax' not in limits or state.T[i] > limits['Tmax']:
                limits['Tmax'] = state.T[i]
            if 'Tmin' not in limits or state.T[i] < limits['Tmin']:
                limits['Tmin'] = state.T[i]
            if 'smax' not in limits or state.s[i] > limits['smax']:
                limits['smax'] = state.s[i]
            if 'smin' not in limits or state.s[i] < limits['smin']:
                limits['smin'] = state.s[i]
            if 'hmax' not in limits or state.h[i] > limits['hmax']:
                limits['hmax'] = state.h[i]
            if 'hmin' not in limits or state.h[i] < limits['hmin']:
                limits['hmin'] = state.h[i]
            _rho = state.d[i]
            if 'rhomax' not in limits or _rho > limits['rhomax']:
                limits['rhomax'] = _rho
            if 'rhomin' not in limits or _rho < limits['rhomin']:
                limits['rhomin'] = _rho
                
            # Get a list of all fluids found in all state instances
            if state.fluid not in all_fluids:
                all_fluids.append(state.fluid)
        
        states.append(dict(p=p,h=h,T=T,rho = rho,s=s,fluids = fluids))
    
    processed['states'] = states
    processed['fluids'] = all_fluids
    processed['limits'] = limits
        
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
            
        ax.plot(range(len(vals)),vals, 'o-', label = label)
        
    ax.legend(loc = 'best')
    
    if fname is not None:
        plt.savefig(fname, dpi = 100)
        
def plot_Ts_at_step(i, processed, fname = None, ax = None, ssatL = None, ssatV = None, Tsat = None):
    """
    Plot each of the profiles at this given time step index of the interpolated data
    """
    if ax is None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        
    ax.plot(ssatV, Tsat, 'k')
    ax.plot(ssatL, Tsat, 'k')        
        
    ax.plot(processed['states'][i]['s'], 
            processed['states'][i]['T'],
            'o')
    
    if fname is not None:
        plt.savefig(fname, dpi = 100)
    
if __name__=='__main__':
    print('I am not meant to be run directly')