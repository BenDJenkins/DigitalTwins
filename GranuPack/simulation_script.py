#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File   : simulation_script.py
# License: GNU v3.0


import os
import math
import numpy as np
import coexist


def calc_bulk_density(calc_positions, calc_radii, calc_diablo_height, diablo_particle_radius):

    positions = calc_positions[~np.isnan(calc_positions).any(axis=1)]  # Remove nans
    radii = calc_radii[~np.isnan(calc_radii)]  # Remove nans
    zpositions_radii_add = np.add(positions[:, 2], radii)
    zpositions_radii_subtract = np.subtract(positions[:, 2], radii)
    highest_particles_indicies = np.argpartition(zpositions_radii_add, -10)[-10:]
    bottom = np.nanmin(zpositions_radii_subtract)
    highest_particle_positions = zpositions_radii_add[highest_particles_indicies]
    top = np.mean(highest_particle_positions)
    if use_multisphere_diablo is True:
        top = top - (calc_diablo_height + diablo_particle_radius)
    length = top - bottom
    total_powder_volume = length*math.pi*tube_internal_radius**2
    calculated_bulk_density = start_mass/total_powder_volume

    return calculated_bulk_density


def generate_diablo(diablo_particle_radius, gen_diablo_height=15/1000, no_layers=1):
    radii = np.linspace(0, 12.4/1000, 20 + 1)
    all_x = []
    all_y = []
    number_of_points = [1, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 170, 180, 190, 200,
                        210]

    for r, radius in enumerate(radii):
        center = [0, 0]
        no_poi = number_of_points[r]
        angle = np.linspace(0, 2 * np.pi, no_poi, endpoint=False)
        x = center[0] + (radius * np.cos(angle))
        y = center[1] + (radius * np.sin(angle))
        all_x.extend(x)
        all_y.extend(y)

    z_value_bottom = 0  # mm
    z_value_top = diablo_height  # mm
    lines = []
    particle_radius = diablo_particle_radius
    pillar_z_values = np.arange(z_value_bottom, z_value_top, particle_radius)

    # Generate particle positions

    for i in range(len(all_x)):
        diablo_line = f'{all_x[i]} {all_y[i]} {z_value_top} {particle_radius}'
        diablo_line_2 = f'{all_x[i]} {all_y[i]} {z_value_bottom} {particle_radius}'
        lines.append(diablo_line)
        lines.append(diablo_line_2)

    for j in range(len(pillar_z_values)):
        diablo_line = f'{0} {0} {pillar_z_values[j]} {particle_radius}'
        lines.append(diablo_line)

    with open('mesh/diablo.txt', 'w') as f:
        for diablo_line_write in lines:
            f.write(f"{diablo_line_write}\n")

    number_of_spheres = len(lines)

    return number_of_spheres


# Generate a new LIGGGHTS simulation from the `granupack_template.sim` template
# User dependent values
nparticles = 15000
drop_distance = 1/1000  # m
no_of_taps = 150
rest_time = 0.2  # Time for particles to settle between drops
t_insert = 1  # Initial time to let particles settle during/after insertion
t_diablo_insert = 0.2  # Time to allow diablo to be inserted into the simulation
save_bulk_density = True  # Save numpy arrays of bulk density
save_all_particle_data = True  # Save particle data. Positions, radii.
use_multisphere_diablo = True  # Use multisphere particles to model the diablo on top of the powder in the GranuPack cell.

# Particle Properties
sliding = 0.3197
rolling = 0.00248
restitution = 0.3
cohesion = 0
density = 1580

# Diablo Properties
tube_internal_radius = 0.026/2  # m
diablo_height = 15/1000  # mm / 1000 to convert to m
diablo_sphere_radius = 0.5/1000  # mm / 1000 to convert to m
diablo_mass = 0.01255  # kg

# Simulation Properties
gravity = 9.81

# Directory to save results to
simulation_dir = os.path.normpath(os.getcwd())

working_dir = f"{simulation_dir}/simulation_files"
if not os.path.isdir(working_dir):
    os.makedirs(working_dir)

results_dir = f"{working_dir}/results"
if not os.path.isdir(results_dir):
    os.makedirs(results_dir)

# Load simulation template lines as a list[str] and modify input parameters
with open(f"{simulation_dir}/granupack_template.sim", "r") as f:
    sim_script = f.readlines()

# Simulation log path
sim_script[1] = f"log {working_dir}/granupack.log\n"
sim_script[10] = f"variable N equal {nparticles}\n"

# Parameter naming:
#    PP  = Particle-Particle
#    PW  = Particle-Wall (cylindrical hull of the GranuPack)
sim_script[21] = f"variable fricPP equal {sliding}\n"
sim_script[22] = f"variable fricPW equal {sliding}\n"
sim_script[23] = f"variable fricPWD equal {0.001}\n"

sim_script[25] = f"variable fricRollPP equal {rolling}\n"
sim_script[26] = f"variable fricRollPW equal {rolling}\n"
sim_script[27] = f"variable fricRollPWD equal {0.001}\n"

sim_script[29] = f"variable corPP equal {restitution}\n"
sim_script[30] = f"variable corPW equal {restitution}\n"
sim_script[31] = f"variable corPWD equal {restitution}\n"
sim_script[31] = f"variable corPWD equal {restitution}\n"

sim_script[33] = f"variable cohPP equal {cohesion}\n"
sim_script[34] = f"variable cohPW equal {cohesion}\n"
sim_script[35] = f"variable cohPWD equal {0}\n"

sim_script[37] = f"variable dens equal {density}\n"
sim_script[39] = f"variable sim_depth equal {(drop_distance*no_of_taps)+0.01}\n"

# Save the simulation template with the modified parameters
sim_path = f"{working_dir}/granupack.sim"
with open(sim_path, "w") as f:
    f.writelines(sim_script)

# Load modified simulation script
sim = coexist.LiggghtsSimulation(sim_path, verbose=True)
line = "\n" + "-" * 80 + "\n"

# Inserting Particles
print(line + "Filling GranuPack cylinder and letting particles settle." + line)
sim.step_to_time(t_insert)  # 2 seconds

if use_multisphere_diablo is True:
    print(line + "Inserting Diablo" + line)

    # Get max particle height
    positions = sim.positions()
    max_z_particle = np.nanmax(positions[:, 2])

    # Generate diablo and calculate diablo density
    no_spheres = generate_diablo(diablo_sphere_radius, gen_diablo_height=diablo_height, no_layers=1)  # Max particle height + 5 mm, 4 layers of particles in the diablo multisphere
    diablo_volume = (4/3*math.pi*diablo_sphere_radius**3)*no_spheres
    diablo_density = diablo_mass/diablo_volume

    # Generate diablo
    sim.execute_command(f'fix ptm1 multispheres particletemplate/multisphere 123457 atom_type 3 density constant {diablo_density} nspheres {no_spheres} ntry 100000 spheres file mesh/diablo.txt scale 1 type 1')
    sim.execute_command('fix pmd multispheres particledistribution/discrete/numberbased 49979693 1 ptm1 1')
    sim.execute_command(f'region diablo cylinder z 0.0 0.0 0.0002 {max_z_particle+0.01} {max_z_particle+0.011}')
    sim.execute_command(f"fix ins1 multispheres insert/pack seed 32452843 distributiontemplate pmd vel constant 0. 0. -0.01. insert_every once overlapcheck yes region diablo particles_in_region 1")
    sim.step_to_time(t_diablo_insert+t_insert)

# Calculate initial mass of particles
initial_radii = sim.radii()
initial_radii = initial_radii[~np.isnan(initial_radii)]  # Remove any nan values from array.
volume = (4 / 3) * np.pi * (initial_radii ** 3)
mass_array = volume * density
start_mass = np.sum(mass_array)  # Mass after all particles inserted
if use_multisphere_diablo is True:
    diablo_volume = ((4 / 3) * math.pi * (diablo_sphere_radius ** 3)) * no_spheres
    apparent_diablo_mass = diablo_volume * density
    start_mass = start_mass - apparent_diablo_mass  # Subtract diablo mass from total mass

# Setup empty arrays to append to
times_array = []
positions_array = []
radii_array = []
velocities_array = []
mass = []
bulk_density = []

# Save initial output data
if save_all_particle_data is True:
    times_array.append(sim.time())
    positions_array.append(sim.positions())
    radii_array.append(sim.radii())
    velocities_array.append(sim.velocities())
if save_bulk_density is True:
    bulk_density.append(calc_bulk_density(calc_positions=sim.positions(),
                                              calc_radii=sim.radii(),
                                              calc_diablo_height=diablo_height,
                                              diablo_particle_radius=diablo_sphere_radius))

# Set the initial time variables
if use_multisphere_diablo is True:
    tlast = t_insert + t_diablo_insert
else:
    tlast = t_insert
discretize = 20
tdrop = 0

# Run the simulation bulk of simulation
print(line + "Starting Tapping!" + line)
droptime = np.sqrt((2*drop_distance)/gravity)  # seconds
for d in range(no_of_taps):

    print("\n\n" + "-" * 80)
    print(f"Tap number: {d}")
    print("-" * 80 + "\n\n")

    # Calculate the times to use during the tapping
    checkpoints = np.linspace(tlast, tlast+droptime, discretize+1)

    # Run the drop
    for t, tdrop in enumerate(checkpoints):
        if t == 0:
            continue
        drop_velocity = gravity*(tdrop-tlast)
        sim.execute_command(f"fix DropTube all move/mesh mesh tube linear 0. 0. -{drop_velocity}")  # Drop tube.
        sim.step_to_time(tdrop)
        sim.execute_command("unfix DropTube")

    # Particle settle time
    t_settle = tdrop + rest_time
    sim.step_to_time(t_settle)
    tlast = t_settle

    # Save output data
    if save_bulk_density is True:
        # Calculate bulk density
        bulk_density_at_d = calc_bulk_density(calc_positions=sim.positions(),
                                              calc_radii=sim.radii(),
                                              calc_diablo_height=diablo_height,
                                              diablo_particle_radius=diablo_sphere_radius)
        # Append bulk density
        bulk_density.append(bulk_density_at_d)

    # Append Particle Data
    if save_all_particle_data is True:
        times_array.append(sim.time())
        radii_array.append(sim.radii())
        positions_array.append(sim.positions())
        velocities_array.append(sim.velocities())

    # Save results as efficient binary NPY-formatted files
    if save_bulk_density is True:
        np.save(f"{results_dir}/bulk_density.npy", bulk_density)

    if save_all_particle_data is True:
        np.save(f"{results_dir}/radii.npy", radii_array)
        np.save(f"{results_dir}/positions.npy", positions_array)

print(line + "Simulation finished running!" + line)
