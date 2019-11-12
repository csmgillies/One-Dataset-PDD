import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def Plot3D(Data):
    fig = plt.figure() #create the pop up window for the plot
    ax = fig.gca(projection='3d') #command to change axes properties

    X = np.asarray(range(0,Data.shape[1])) #create 0-length axis
    Y = np.asarray(range(0,Data.shape[0])) #create 0-height axis

    X, Y = np.meshgrid(X, Y) #creates coordinates required to plot

    surf = ax.plot_surface(X, Y, Data, cmap=cm.coolwarm, linewidth=0, antialiased=False) #creates plot

    fig.colorbar(surf, shrink=0.5, aspect=5) #makes plot look pretty
    plt.show()
