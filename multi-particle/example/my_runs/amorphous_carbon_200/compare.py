import numpy as np 
import matplotlib.pyplot as plt

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

# finding where the polarization peaks
print(pol_nick[np.nanargmax(pol_nick)])
print(pol_danielle[np.nanargmax(pol_danielle)])

# plot the data
fig, axes = plt.subplots(2,1)

axes[0].plot(angle_nick, s11_nick, label="nick")
axes[0].plot(angle_danielle, s11_danielle, label="danielle")

axes[1].plot(angle_nick, pol_nick, label="nick")
axes[1].plot(angle_danielle, pol_danielle, label="danielle")

axes[0].set_yscale("log")

axes[0].set_xlabel("Scattering angle (deg)")
axes[0].set_ylabel("S11")
axes[1].set_xlabel("Scattering angle (deg)")
axes[1].set_ylabel("-S12/S11")

axes[0].legend()
axes[1].legend()
plt.tight_layout()
plt.savefig("comparison.png", dpi=150)
plt.show()

