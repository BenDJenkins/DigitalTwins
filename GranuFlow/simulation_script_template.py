#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File   : simulation_script_template.py
# License: GNU v3.0


import os

import numpy as np
import coexist


# Generate a new LIGGGHTS simulation from the `granuflow_template.sim` template
nparticles = 130000

sliding = 0.2
rolling = 0.01
restitution = 0.5
cohesion = 1000

density = 1000

orifice_size = 2

# Directory to save results to
results_dir = f"results_{orifice_size}mm"
if not os.path.isdir(results_dir):
    os.mkdir(results_dir)


# Load simulation template lines as a list[str] and modify input parameters
with open("granuflow_template.sim", "r") as f:
    sim_script = f.readlines()


# Simulation log path
sim_script[1] = f"log {results_dir}/granuflow.log\n"
sim_script[10] = f"variable N equal {nparticles}\n"


# Parameter naming:
#    PP  = Particle-Particle
#    PW  = Particle-Wall (cylindrical hull of the granuflow)
#    PSW = Particle-Sidewall (circular sides of the granuflow)
sim_script[22] = f"variable fricPP equal {sliding}\n"
sim_script[23] = f"variable fricPW equal {sliding}\n"
sim_script[24] = f"variable fricPSW equal {sliding}\n"

sim_script[27] = f"variable fricRollPP equal {rolling}\n"
sim_script[28] = f"variable fricRollPW equal {rolling}\n"
sim_script[29] = f"variable fricRollPSW equal {rolling}\n"

sim_script[32] = f"variable corPP equal {restitution}\n"
sim_script[33] = f"variable corPW equal {restitution}\n"
sim_script[34] = f"variable corPSW equal {restitution}\n"

sim_script[37] = f"variable cohPP equal {cohesion}\n"
sim_script[38] = f"variable cohPW equal {cohesion}\n"
sim_script[39] = f"variable cohPSW equal {cohesion}\n"

sim_script[42] = f"variable dens equal {density}\n"

sim_script[134] = f"fix	plate	all mesh/surface file mesh/Plate{orifice_size}mm.stl	type 2  scale 0.001\n"


# Save the simulation template with the modified parameters
sim_path = f"{results_dir}/granuflow.sim"
with open(sim_path, "w") as f:
    f.writelines(sim_script)


# Load modified simulation script
sim = coexist.LiggghtsSimulation(sim_path, verbose=True)


# Run simulation up to given time (s)
line = "\n" + "-" * 80 + "\n"

print(line + "Pouring particles and letting them settle" + line)
sim.step_to_time(20.0)

print(line + "Letting remaining falling particles settle" + line)
sim.step_to_time(21.0)  # Letting remaining falling particles settle.

print(line + "Moving GranuFlow plate and letting particles flow" + line)

times = []
positions = []
radii = []
velocities = []

sim.execute_command("fix MovePlate all move/mesh mesh plate linear -0.025 0. 0.")  # Move GranuFlow plate.

checkpoints_open = np.arange(21.0, 23.0, 1/120)

for t in checkpoints_open:
    sim.step_to_time(t)

    times.append(sim.time())
    radii.append(sim.radii())
    positions.append(sim.positions())
    velocities.append(sim.velocities())

sim.execute_command("unfix MovePlate")

start_time = 23.0
end_time = 28.0

checkpoints = np.arange(start_time, end_time, 1 / 120)

for t in checkpoints:
    sim.step_to_time(t)

    times.append(sim.time())
    radii.append(sim.radii())
    positions.append(sim.positions())
    velocities.append(sim.velocities())

# Save results as efficient binary NPY-formatted files
np.save(f"{results_dir}/times_{orifice_size}mm.npy", times)
np.save(f"{results_dir}/radii_{orifice_size}mm.npy", radii)
np.save(f"{results_dir}/positions_{orifice_size}mm.npy", positions)
np.save(f"{results_dir}/velocities_{orifice_size}mm.npy", velocities)
