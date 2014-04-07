import matplotlib.pyplot as plt

def imshow(x):
    return plt.imshow(x, interpolation='none', aspect='auto', cmap='hot', origin='lower')
