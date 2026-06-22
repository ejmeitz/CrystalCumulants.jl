from os.path import join

from cumulant_analysis import crystal_thermodynamic_properties

f_kmesh = [15, 15, 15]
nconf = 100_000
nboot = 5000
maximum_frequency = 2.5 # THz
n_iter = 10
r_cut = 6.955

quantum = True
base_outpath = "/home/emeitz/Neon_ANALYTICAL_PIMD"
getoutpath = lambda T: join(base_outpath, f"T{T}")

n_seeds = 5

Ts = [4, 24]
pot_cmds = [
    "pair_style lj/cut 6.955",
    "pair_coeff * * 0.0032135 2.782",
    "pair_modify shift yes",
]

## sTDEP IFCs
outpath_T = lambda T: join(base_outpath, f"T{T}", f"seed{seed}")

ifc_basepath = lambda T: f"/home/emeitz/Neon_sTDEP/results/T{T}"
ucposcar_path = lambda T: join(ifc_basepath(T), "infile.ucposcar")
ssposcar_path = lambda T: join(ifc_basepath(T), "infile.ssposcar")

ifc2_path = lambda T: join(ifc_basepath(T), "infile.forceconstant")
ifc3_path = lambda T: join(ifc_basepath(T), "infile.forceconstant_thirdorder")
ifc4_path = lambda T: join(ifc_basepath(T), "infile.forceconstant_fourthorder")

# FIT sTDEP IFCs 

for seed in range(n_seeds):

    outpath_T = lambda T: join(base_outpath, f"T{T}", f"seed{seed}")
    mkpath(outpath_T)

    make_stdep_ifcs(
            joinpath(outpath_T, "infile.ucposcar"),
            joinpath(outpath_T, "infile.ssposcar"),
            outpath_T,
            pot_cmds,
            n_iter,
            r_cut,
            T,
            maximum_frequency,
            quantum
        )

    # GET THERMO PROPERTIES

    crystal_thermodynamic_properties(
        Ts,
        getoutpath,
        ucposcar_path,
        ssposcar_path,
        ifc2_path,
        ifc3_path,
        ifc4_path,
        pot_cmds,
        quantum=quantum,
        nconf=nconf,
        nboot=nboot,
        size_study=True,
        free_energy_q_mesh=f_kmesh,
    )
