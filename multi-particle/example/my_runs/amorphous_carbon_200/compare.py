import numpy as np 
import pyplot.matplotlib as plt

# nick's file
nick = np.loadtxt("outputS.out")

angle_nick = nick[:, 0]
s11_nick = nick[:, 1]
s12_nick = nick[:, 2]

# danielle's file
danielle = np.loadtxt("../../batch_runs/amorphous_carbon_200/outputS.out")

angle_danielle = danielle[:, 0]
s11_danielle = danielle[:, 1]
s12_danielle = danielle[:, 2]

# compute polarization from nick's data
pol_nick = (-s12_nick) / s11_nick

# compute polarization from danielle's data
pol_danielle = (-s12_danielle) / s11_danielle

print(pol_nick[11])
