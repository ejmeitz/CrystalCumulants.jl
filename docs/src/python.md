# Python

@id Python

Python wrapper for [CrystalCumulants.jl](https://github.com/ejmeitz/CrystalCumulants.jl).

Julia dependencies are managed automatically by [juliacall](https://juliapy.github.io/PythonCall.jl/stable/juliacall/) via `juliapkg.json` in the package. On first use, juliacall sets up a Julia environment and installs `CrystalCumulants` and its dependencies (including LAMMPS). This may take a few minutes. If you have NVIDIA GPUs, a CUDA artifact may be installed; it is not used by this package.

!!! warning
    1. Set `PYTHON_JULIACALL_HANDLE_SIGNALS=yes` in your environment, or Python cannot pass threads through to Julia. Ctrl-C will not stop the process; you may need to kill it manually.
    2. Set `PYTHON_JULIACALL_THREADS=<n-threads>` to control Julia thread count (default is 1). You may also need `JULIA_NUM_THREADS`.

## Requirements

- Python 3.10+
- Linux (macOS may work; Windows is not supported)

## Installation

From the repository root:

```bash
pip install -e ./python
```

```python
from cumulant_analysis import make_stdep_ifcs, crystal_thermodynamic_properties
```

## API

### `make_stdep_ifcs`

Generate self-consistent TDEP force constants with sTDEP.

```python
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
    rc4,
    **kwargs,
)
```

| Argument | Description |
|----------|-------------|
| `ucposcar_path` | Path to unit-cell POSCAR (TDEP format) |
| `ssposcar_path` | Path to supercell POSCAR (TDEP format) |
| `outdir` | Output directory for sTDEP results |
| `pot_cmds` | LAMMPS potential commands (`list[str]`) |
| `n_iter` | Number of self-consistent sTDEP iterations |
| `r_cut` | Pair potential cutoff used by sTDEP for 2nd-order IFCs |
| `T` | Temperature (K) |
| `maximum_frequency` | Maximum frequency for the initial IFC guess |
| `quantum` | Sample quantum (`True`) or classical (`False`) configurations |
| `rc3` | Cutoff radius for 3rd-order IFC fitting |
| `rc4` | Cutoff radius for 4th-order IFC fitting |
| `**kwargs` | Additional keyword arguments forwarded to sTDEP (e.g. `mix`, `nconf_init`, `max_configs`) |

Output files are written under `outdir`, including 2nd- through 4th-order IFCs.

### `crystal_thermodynamic_properties`

Calculate thermodynamic properties across a temperature range using the free energy cumulant expansion.

```python
crystal_thermodynamic_properties(
    temperatures,
    outpath,
    ucposcar_path,
    ssposcar_path,
    ifc2_path,
    ifc3_path,
    ifc4_path,
    pot_cmds,
    *,
    quantum=False,
    nconf=100_000,
    nboot=2500,
    size_study=False,
    harmonic_q_mesh=(30, 30, 30),
    free_energy_q_mesh=(25, 25, 25),
    n_threads=None,
)
```

Path-like parameters may be a `str` or a callable `T -> path` for temperature-dependent inputs:

```python
ucposcar_path = lambda T: f"/home/data/T{int(T)}/infile.ucposcar"
```

| Keyword | Default | Description |
|---------|---------|-------------|
| `quantum` | `False` | Quantum (`True`) or classical (`False`) statistics |
| `nconf` | `100_000` | Configurations sampled for the 0th-order correction |
| `nboot` | `2500` | Bootstrap samples for 0th-order standard error |
| `size_study` | `False` | If `True`, write 0th-order correction vs. sample count |
| `harmonic_q_mesh` | `(30, 30, 30)` | q-mesh for harmonic contribution |
| `free_energy_q_mesh` | `(25, 25, 25)` | q-mesh for 1st- and 2nd-order corrections |
| `n_threads` | all Julia threads | Julia thread count |

**Results are written to disk** (`F_mean.txt`, `U_mean.txt`, `S_mean.txt`, `Cv_mean.txt`) and are not returned to Python.

## Output files

For each property, the code writes `F_mean.txt`, `U_mean.txt`, `S_mean.txt`, and `Cv_mean.txt` with rows broken down into harmonic (`F0`, etc.), 0th-order offset, 1st-order, 2nd-order, and total. Only the 0th-order correction has an associated bootstrap standard error. HDF5 versions (`.h5`) are also written.

If `size_study=True`, an additional file reports the 0th-order correction as a function of sample count (useful for convergence checks).

## Solid Neon example

Clone the repository for bundled input files:

```
git clone --depth 1 --branch v0.1.0 https://github.com/ejmeitz/CrystalCumulants.jl.git
```

Run the examples below from the repository root (update `repo_root` and `outpath`).

### sTDEP IFCs

The first step is to obtain 2nd-, 3rd-, and 4th-order force constants from sTDEP. Skip to [Thermodynamic properties](#Thermodynamic-properties) if you already have IFCs. The method expects self-consistent phonons (sTDEP or SSCHA); MD-TDEP or finite-difference IFCs are far less accurate.

An in-depth sTDEP tutorial is [here](https://github.com/tdep-developers/tdep-tutorials/tree/main/02_sampling). A multi-volume, multi-temperature workflow used in the paper is in [`workflows/neon_lattice_params_stdep.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon_lattice_params_stdep.jl).

Precomputed force constants are in [`data/stdep_results`](https://github.com/ejmeitz/CrystalCumulants.jl/tree/main/data/stdep_results) (`iter009` folder; ~2 minutes to reproduce).

```python
from os.path import join

from cumulant_analysis import make_stdep_ifcs

repo_root = "<path-to-repo-root>"  # UPDATE
outpath = "<whatever-directory-you-want>"  # UPDATE

T = 24.0  # Kelvin

r_cut = 6.955
rc3 = r_cut # cutoff for third-order IFCs
rc4 = 4.0  # cutoff for fourth-order IFCs
pot_cmds = [
    f"pair_style lj/cut {r_cut}",
    "pair_coeff * * 0.0032135 2.782",
    "pair_modify shift yes",
]

n_iter = 10
maximum_frequency = 2.5
quantum = True
# Other sTDEP kwargs:
# - mix=True           — mix configs from prior step with current step
# - nconf_init=8       — configs for iteration 0
# - max_configs=512    — max configs per iteration (doubles each iter)

basepath = join(repo_root, "data", "stdep_inputs")
ssposcar_path = join(basepath, "infile.ssposcar")
ucposcar_path = join(basepath, "infile.ucposcar")

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

A multi-temperature workflow is in [`workflows/neon.py`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon.py) (Python port of [`workflows/neon.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon.jl)).

```python
from os.path import join

from cumulant_analysis import crystal_thermodynamic_properties

repo_root = "<path-to-repo-root>"  # UPDATE
outpath = "<whatever-directory-you-want>"  # UPDATE
basepath = join(repo_root, "data", "thermo_inputs")

T = 24.0  # Kelvin

r_cut = 6.955
pot_cmds = [
    f"pair_style lj/cut {r_cut}",
    "pair_coeff * * 0.0032135 2.782",
    "pair_modify shift yes",
]

nconf = 100_000
nboot = 5000
size_study = True
harmonic_q_mesh = (30, 30, 30)
free_energy_q_mesh = (15, 15, 15)  # ~15×15×15 is often sufficient

ssposcar_path = join(basepath, "infile.ssposcar")
ucposcar_path = join(basepath, "infile.ucposcar")

ifc2_path = join(basepath, "infile.forceconstant")
ifc3_path = join(basepath, "infile.forceconstant_thirdorder")
ifc4_path = join(basepath, "infile.forceconstant_fourthorder")

crystal_thermodynamic_properties(
    [T],
    outpath,
    ucposcar_path,
    ssposcar_path,
    ifc2_path,
    ifc3_path,
    ifc4_path,
    pot_cmds,
    quantum=True,
    nconf=nconf,
    nboot=nboot,
    size_study=size_study,
    harmonic_q_mesh=harmonic_q_mesh,
    free_energy_q_mesh=free_energy_q_mesh,
)
```

### Temperature-dependent paths

When IFCs and structures vary with temperature, pass callables instead of fixed paths:

```python
from os.path import join

base = "/data/stdep/RESULTS"

crystal_thermodynamic_properties(
    [100.0, 200.0, 300.0],
    lambda T: f"/out/T{int(T)}",
    lambda T: join(base, f"T{int(T)}_0", "infile.ucposcar"),
    lambda T: join(base, f"T{int(T)}_0", "infile.ssposcar"),
    lambda T: join(base, f"T{int(T)}_0", "infile.forceconstant"),
    lambda T: join(base, f"T{int(T)}_0", "infile.forceconstant_thirdorder"),
    lambda T: join(base, f"T{int(T)}_0", "infile.forceconstant_fourthorder"),
    pot_cmds,
)
```

## Related scripts

| Script | Description |
|--------|-------------|
| [`workflows/neon.py`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon.py) | Multi-temperature Neon thermodynamics |
| [`workflows/neon_benchmark.py`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon_benchmark.py) | Benchmark / seed study |
| [`workflows/neon.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon.jl) | Julia version of the multi-temperature workflow |
| [`workflows/neon_lattice_params_stdep.jl`](https://github.com/ejmeitz/CrystalCumulants.jl/blob/main/workflows/neon_lattice_params_stdep.jl) | Volume/temperature sTDEP loop (paper workflow) |

See also the [Theory](@ref Theory) page and [Julia](@ref Julia) walkthrough.
