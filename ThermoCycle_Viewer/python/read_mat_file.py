import scipy.io
import matplotlib.pyplot as plt

def transpose_strings(name):
    cols = []
    
    def get_col(i):
        return [row[i] for row in name]
    
    for i in range(len(name[0])):
        cols.append(''.join(get_col(i)).strip())
    
    return cols
    
data = scipy.io.loadmat('sample_results.mat')

# print scipy.io.whosmat('sample_results.mat')
# for key in data.keys():
#     print key, data[key].shape

# Get the names and descriptions, and then transpose them and turn them each into lists
names = transpose_strings(data['name'])
descriptions = transpose_strings(data['description'])

# Get the data and join it into 
data_2 = data['data_2']
t = data_2[0]
for i in range(10, 16):
    plt.plot(t, data_2[i], label = names[i]+descriptions[i])
    
plt.legend(loc = 'best')
plt.show()