# Julia

@id Julia

## Requirements

- Linux (macOS may work; Windows is not supported)
- Julia 1.10+
- Set `JULIA_NUM_THREADS` before launching Julia for parallel execution

## Installation

```julia
using Pkg
Pkg.add(; url = "https://github.com/ejmeitz/LatticeDynamicsToolkit.jl.git", rev = "v0.1.2")
Pkg.add(; url = "https://github.com/ejmeitz/CrystalCumulants.jl.git", rev = "v0.1.1")
```

## API

### `make_stdep_ifcs`

Generate self-consistent TDEP force constants with sTDEP.

```julia
make_stdep_ifcs(
    ucposcar_path,
    ssposcar_path,
    outdir,
    pot_cmds,
    n_iter,
    r_cut,
    T,
    maximum_frequency,
    quantum,
    rc3,
    rc4;
    kwargs...
)
```

| Argument | Description |
|----------|-------------|
| `ucposcar_path` | Path to unit-cell POSCAR (TDEP format) |
| `ssposcar_path` | Path to supercell POSCAR (TDEP format) |
| `outdir` | Output directory for sTDEP results |
| `pot_cmds` | LAMMPS potential commands (`Vector{String}`) |
| `n_iter` | Number of self-consistent sTDEP iterations |
| `r_cut` | Pair potential cutoff used by sTDEP |
| `T` | Temperature (K) |
| `maximum_frequency` | Maximum frequency for the initial IFC guess |
| `quantum` | Sample quantum (`true`) or classical (`false`) configurations |
| `rc3` | Cutoff radius for 3rd-order IFC fitting |
| `rc4` | Cutoff radius for 4th-order IFC fitting |
| `kwargs...` | Additional keyword arguments forwarded to sTDEP (e.g. `mix`, `nconf_init`, `max_configs`) |

Output files are written under `outdir`. This step produces 2nd-4th order sTDEP IFCs.

### `crystal_thermodynamic_properties`

Calculate thermodynamic properties across a temperature range using the free energy cumulant expansion.

```julia
crystal_thermodynamic_properties(
    temperatures,
    outpath,
    ucposcar_path,
    ssposcar_path,
    ifc2_path,
    ifc3_path,
    ifc4_path,
    pot_cmds;
    quantum = false,
    nconf = 100_000,
    nboot = 2500,
    size_study = false,
    harmonic_q_mesh = [30, 30, 30],
    free_energy_q_mesh = [25, 25, 25],
    n_threads = Threads.nthreads(),
)
```

All path-like parameters may be a `String` or a function `(T) -> path` for temperature-dependent inputs:

```julia
ucposcar_path = (T) -> joinpath("/home/data", "T$(Int(T))", "infile.ucposcar")
```

| Keyword | Default | Description |
|---------|---------|-------------|
| `quantum` | `false` | Use quantum (`true`) or classical (`false`) statistics |
| `nconf` | `100_000` | Configurations sampled for the 0th-order correction |
| `nboot` | `2500` | Bootstrap samples for 0th-order standard error |
| `size_study` | `false` | If `true`, write 0th-order correction vs. sample count |
| `harmonic_q_mesh` | `[30, 30, 30]` | q-mesh for harmonic contribution |
| `free_energy_q_mesh` | `[25, 25, 25]` | q-mesh for 1st- and 2nd-order corrections |
| `n_threads` | `Threads.nthreads()` | Parallel threads (set `JULIA_NUM_THREADS` in the environment) |

## Output files

For each property, the code writes `F_mean.txt`, `U_mean.txt`, `S_mean.txt`, and `Cv_mean.txt` with rows broken down into harmonic (`F0`, etc.), 0th-order offset, 1st-order, 2nd-order, and total. Only the 0th-order correction has an associated bootstrap standard error. HDF5 versions (`.h5`) are also written.

If `size_study = true`, an additional file reports the 0th-order correction as a function of sample count (useful for convergence checks).

## Solid Neon example

Clone the repository for bundled input files:

```
git clone --depth 1 --branch v0.1.0 https://github.com/ejmeitz/CrystalCumulants.jl.git
```

### sTDEP IFCs

The first step is to obtain 2nd-, 3rd-, and 4th-order force constants from sTDEP. Skip to [Thermodynamic properties](#Thermodynamic-properties) if you already have IFCs. The method expects self-consistent phonons (sTDEP or SSCHA); MD-TDEP or finite-difference IFCs are far less accurate.

An in-depth sTDEP tutorial is [here](https://github.com/tdep-developers/tdep-tutorials/tree/main/02_sampling). A multi-volume, multi-temperature workflow used in the paper is in [`workflows/neon_lattice_params_stdep.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon_lattice_params_stdep.jl).

Precomputed force constants are in [`data/stdep_results`](https://github.com/ejmeitz/CrystalCumulants.jl/tree/main/data/stdep_results) (`iter009` folder; ~2 minutes to reproduce).

```julia
using CrystalCumulants

repo_root = "<path-to-repo-root>"  # UPDATE
outpath = "<whatever-directory-you-want>"  # UPDATE

T = 24  # Kelvin

r_cut = 6.955
rc3 = r_cut # cutoff for third-order IFCs
rc4 = 4.0 # cutoff for fourth-order IFCs
pot_cmds = [
    "pair_style lj/cut $(r_cut)",
    "pair_coeff * * 0.0032135 2.782",
    "pair_modify shift yes"
]

n_iter = 10
maximum_frequency = 2.5
quantum = true
# Other sTDEP kwargs:
# - mix = true          — mix configs from prior step with current step
# - nconf_init = 8      — configs for iteration 0
# - max_configs = 512   — max configs per iteration (doubles each iter)

basepath = joinpath(repo_root, "data", "stdep_inputs")
ssposcar_path = joinpath(basepath, "infile.ssposcar")
ucposcar_path = joinpath(basepath, "infile.ucposcar")

make_stdep_ifcs(
    ucposcar_path,
    ssposcar_path,
    outpath,
    pot_cmds,
    n_iter,
    r_cut,
    T,
    maximum_frequency,
    quantum,
    rc3,
    rc4,
)
```

### Thermodynamic properties

Use IFCs from above or the bundled set in [`data/thermo_inputs`](https://github.com/ejmeitz/CrystalCumulants.jl/tree/main/data/thermo_inputs). Expected free energy at 24 K is roughly **−0.0179270 eV/atom** (stochastic; first few decimals should match). ~3 minutes on 40 cores. Reference results: [`data/thermo_results`](https://github.com/ejmeitz/CrystalCumulants.jl/tree/main/data/thermo_results) (25×25×25 free-energy mesh).

A multi-temperature workflow is in [`workflows/neon.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon.jl).

```julia
using CrystalCumulants

repo_root = "<path-to-repo-root>"  # UPDATE
outpath = "<whatever-directory-you-want>"  # UPDATE
basepath = joinpath(repo_root, "data", "thermo_inputs")

T = 24  # Kelvin

r_cut = 6.955
pot_cmds = [
    "pair_style lj/cut $(r_cut)",
    "pair_coeff * * 0.0032135 2.782",
    "pair_modify shift yes"
]

nconf = 100_000
nboot = 5000
size_study = true
harmonic_q_mesh = [30, 30, 30]
free_energy_q_mesh = [15, 15, 15]  # ~15×15×15 is often sufficient

ssposcar_path = joinpath(basepath, "infile.ssposcar")
ucposcar_path = joinpath(basepath, "infile.ucposcar")

ifc2_path = joinpath(basepath, "infile.forceconstant")
ifc3_path = joinpath(basepath, "infile.forceconstant_thirdorder")
ifc4_path = joinpath(basepath, "infile.forceconstant_fourthorder")

crystal_thermodynamic_properties(
    [T],
    outpath,
    ucposcar_path,
    ssposcar_path,
    ifc2_path,
    ifc3_path,
    ifc4_path,
    pot_cmds;
    quantum = true,
    nconf = nconf,
    nboot = nboot,
    size_study = size_study,
    harmonic_q_mesh = harmonic_q_mesh,
    free_energy_q_mesh = free_energy_q_mesh,
)
```

## Related workflows

| Script | Description |
|--------|-------------|
| [`workflows/neon.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon.jl) | Multi-temperature Neon thermodynamics |
| [`workflows/neon_lattice_params_stdep.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon_lattice_params_stdep.jl) | Volume/temperature sTDEP loop (paper workflow) |
| [`workflows/silicon.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/silicon.jl) | Silicon example |
| [`workflows/kmesh_studies.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/kmesh_studies.jl) | q-mesh convergence studies |

See also the [Theory](@ref Theory) page and [Python](@ref Python) wrapper.
