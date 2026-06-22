# Python

@id Python

Python wrapper for [CumulantAnalysis.jl](https://github.com/ejmeitz/CumulantAnalysis.jl).

Julia dependencies are managed automatically by [juliacall](https://juliapy.github.io/PythonCall.jl/stable/juliacall/) via `juliapkg.json` in the package. On first use, juliacall sets up a Julia environment and installs `CumulantAnalysis` and its dependencies (including LAMMPS). This may take a few minutes. If you have NVIDIA GPUs, a CUDA artifact may be installed; it is not used by this package.

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
    **kwargs,
)
```

Generates self-consistent TDEP 2nd-order force constants. Additional `**kwargs` are forwarded to the underlying sTDEP call. Output files are written under `outdir`.

### `crystal_thermodynamic_properties`

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

Path-like parameters may be strings or callables `T -> path` for temperature-dependent inputs.

| Keyword | Default | Description |
|---------|---------|-------------|
| `quantum` | `False` | Quantum (`True`) or classical (`False`) statistics |
| `nconf` | `100_000` | Configurations for the 0th-order correction |
| `nboot` | `2500` | Bootstrap samples for 0th-order error |
| `size_study` | `False` | 0th-order correction vs. sample count |
| `harmonic_q_mesh` | `(30, 30, 30)` | q-mesh for harmonic contribution |
| `free_energy_q_mesh` | `(25, 25, 25)` | q-mesh for cumulant corrections |
| `n_threads` | all Julia threads | Julia thread count |

**Results are written to disk** (`F_mean.txt`, `U_mean.txt`, `S_mean.txt`, `Cv_mean.txt`) and are not returned to Python.

## Usage

The [`workflows/neon.jl`](https://github.com/ejmeitz/CumulantAnalysis.jl/blob/main/workflows/neon.jl) example is ported in [`workflows/neon.py`](https://github.com/ejmeitz/CumulantAnalysis.jl/blob/main/workflows/neon.py). A single-temperature example:

```python
from cumulant_analysis import make_stdep_ifcs, crystal_thermodynamic_properties

pot_cmds = [
    "pair_style lj/cut 6.955",
    "pair_coeff * * 0.0032135 2.782",
    "pair_modify shift yes",
]

make_stdep_ifcs(
    "data/stdep_inputs/infile.ucposcar",
    "data/stdep_inputs/infile.ssposcar",
    "out/stdep",
    pot_cmds,
    n_iter=10,
    r_cut=6.955,
    T=24.0,
    maximum_frequency=2.5,
    quantum=True,
)

crystal_thermodynamic_properties(
    [24.0],
    "out/thermo",
    "data/thermo_inputs/infile.ucposcar",
    "data/thermo_inputs/infile.ssposcar",
    "data/thermo_inputs/infile.forceconstant",
    "data/thermo_inputs/infile.forceconstant_thirdorder",
    "data/thermo_inputs/infile.forceconstant_fourthorder",
    pot_cmds,
    quantum=True,
    nconf=100_000,
    size_study=True,
)
```

### Temperature-dependent paths

```python
base = "/data/stdep/RESULTS"
crystal_thermodynamic_properties(
    [100, 200, 300],
    lambda T: f"/out/T{int(T)}",
    lambda T: f"{base}/T{int(T)}_0/infile.ucposcar",
    lambda T: f"{base}/T{int(T)}_0/infile.ssposcar",
    lambda T: f"{base}/T{int(T)}_0/infile.forceconstant",
    lambda T: f"{base}/T{int(T)}_0/infile.forceconstant_thirdorder",
    lambda T: f"{base}/T{int(T)}_0/infile.forceconstant_fourthorder",
    pot_cmds,
)
```

## Related scripts

| Script | Description |
|--------|-------------|
| [`workflows/neon.py`](https://github.com/ejmeitz/CumulantAnalysis.jl/blob/main/workflows/neon.py) | Multi-temperature Neon example (Python port of `neon.jl`) |
| [`workflows/neon_benchmark.py`](https://github.com/ejmeitz/CumulantAnalysis.jl/blob/main/workflows/neon_benchmark.py) | Benchmark script |

For theory and the full Julia walkthrough, see [Theory](@ref Theory) and [Julia](@ref Julia).
