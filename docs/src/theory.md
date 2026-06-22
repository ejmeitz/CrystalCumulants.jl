# [Theory](@id Theory)


## Overview

Accurate finite-temperature calculations of vibrational thermodynamic properties require both anharmonic effects (phonon–phonon scattering, frequency renormalization) and quantum nuclear effects (Bose–Einstein statistics, zero-point motion). Harmonic phonon theories provide a quantum description but neglect intrinsic anharmonicity. Path-integral molecular dynamics combined with thermodynamic integration (TI) captures both effects but is expensive, and TI yields free energy directly—entropy, internal energy, and heat capacity then require additional numerical differentiation and simulations.

The free energy cumulant expansion offers a computationally tractable alternative. Combined with renormalized self-consistent interatomic force constants (IFCs), exact evaluation of the first and second cumulants, and a rapidly convergent estimator for the reference potential energy, it estimates free energy, entropy, internal energy, and heat capacity **without** molecular dynamics or PIMD during IFC fitting or property evaluation.

CrystalCumulants.jl implements this workflow using sTDEP IFCs for the harmonic reference and sampling-based estimators for the temperature dependence of the reference energy ``V_0``.

## Thermodynamic quantities

For a system with fixed particle number ``N``, volume ``V``, and temperature ``T``, the relevant thermodynamic potential is the Helmholtz free energy ``\mathcal{F}``:

```math
\mathcal{F} = \mathcal{U} - T\mathcal{S},
```

where ``\mathcal{U}`` is the internal energy and ``\mathcal{S}`` is the entropy. Entropy, internal energy, and heat capacity ``C_V`` follow from derivatives of ``\mathcal{F}``:

```math
\mathcal{S} = -\frac{\partial\mathcal{F}}{\partial T}, \qquad
\mathcal{U} = \frac{\partial(\beta\mathcal{F})}{\partial\beta}, \qquad
C_V = -T\frac{\partial^2\mathcal{F}}{\partial T^2},
```

with ``\beta = (k_\mathrm{B} T)^{-1}``. Throughout, ``\mathcal{F}``, ``\mathcal{S}``, ``\mathcal{U}``, and ``C_V`` denote **vibrational** contributions only (electronic and magnetic degrees of freedom are neglected).

## Vibrational free energy decomposition

The vibrational free energy is written as

```math
\mathcal{F}_\mathrm{vib} = V_0 + \mathcal{F}_\mathrm{H} + \mathcal{F}_\mathrm{anh},
```

where:

- ``V_0`` is a reference potential energy
- ``\mathcal{F}_\mathrm{H}`` is the harmonic free energy
- ``\mathcal{F}_\mathrm{anh}`` is the anharmonic correction

The level of theory determines how each term is defined.

### Harmonic free energy ``\mathcal{F}_\mathrm{H}``

The harmonic contribution is a sum over phonon modes:

```math
\mathcal{F}_\mathrm{H} = \sum_{\mathbf{k}\lambda} \left[\frac{\hbar\omega_{\mathbf{k}\lambda}}{2} + \beta^{-1}\log\!\left(1-e^{-\beta\hbar\omega_{\mathbf{k}\lambda}}\right)\right],
```

where ``\omega_{\mathbf{k}\lambda}`` is the frequency of the mode with wavevector ``\mathbf{k}`` on branch ``\lambda``. In CrystalCumulants.jl, ``\mathcal{F}_\mathrm{H}`` (and the corresponding ``\mathcal{S}_\mathrm{H}``, ``\mathcal{U}_\mathrm{H}``, ``C_{V,\mathrm{H}}``) are obtained by Brillouin-zone integration over renormalized phonon frequencies from the second-order IFCs. The `harmonic_q_mesh` keyword controls this grid.

Under the quantum harmonic approximation (HA), ``V_0`` is the potential energy at mechanical equilibrium and ``\mathcal{F}_\mathrm{anh} = 0``. Because ``V_0`` is temperature independent in the HA, it does not contribute to ``\mathcal{S}``, ``\mathcal{U}``, or ``C_V``.

### Renormalized IFCs and reference energies

Accuracy improves when IFCs are renormalized to finite temperature, e.g. via TDEP or stochastic TDEP (sTDEP). With renormalized IFCs, ``V_0`` captures the average effect of anharmonicity omitted from the harmonic reference:

| Method | Reference energy |
|--------|------------------|
| sTDEP (harmonic ensemble) | ``V_0 = \langle V - V_2 \rangle_\mathrm{H}`` |
| MD-TDEP (true ensemble) | ``V_0 = \langle V - V_2 \rangle`` |

Here ``V`` is the true potential energy and ``V_2`` is the harmonic Taylor term (including polar interactions where applicable). The ensemble average must match the Hamiltonian used to fit the IFCs. ``V_1 = 0`` at equilibrium.

Setting ``\mathcal{F}_\mathrm{anh} = 0`` gives the renormalized harmonic free energies:

```math
\mathcal{F}^{\,\mathrm{sTDEP}} = \langle V - V_2 \rangle_\mathrm{H} + \mathcal{F}_\mathrm{H}, \qquad
\mathcal{F}^{\,\mathrm{MD-TDEP}} = \langle V - V_2 \rangle + \mathcal{F}_\mathrm{H}.
```

sTDEP samples the harmonic ensemble directly (no MD/PIMD for the free energy itself). These renormalized harmonic models capture mean anharmonic shifts through ``V_0`` but not fluctuations beyond the harmonic reference.

## Free energy cumulant expansion

To include cubic and quartic anharmonicity while retaining quantum statistics, the vibrational free energy is approximated by the cumulant expansion truncated at second order:

```math
\mathcal{F} \approx V_0 + \mathcal{F}_\mathrm{H} + \mathcal{F}_1 + \mathcal{F}_2.
```

| Term | Role |
|------|------|
| ``V_0`` | Reference potential energy (0th-order / constant correction) |
| ``\mathcal{F}_\mathrm{H}`` | Harmonic free energy from renormalized phonons |
| ``\mathcal{F}_1`` | First cumulant — quartic anharmonicity |
| ``\mathcal{F}_2`` | Second cumulant — cubic anharmonicity |

When the potential is represented by a Taylor effective potential truncated beyond fourth order (``V \approx V_0 + V_2 + V_3 + V_4``), ``\mathcal{F}_1`` is determined by quartic terms and ``\mathcal{F}_2`` by cubic terms. The second-order cumulant expansion extends the sTDEP free energy to include these anharmonic contributions.

A key advantage is **direct access** to ``\mathcal{S}``, ``\mathcal{U}``, and ``C_V`` from analytical and sampling-based derivatives of ``\mathcal{F}``, without numerical differentiation of a simulated free energy.

### Method comparison

| | HA | ``\mathcal{F}^{\,\mathrm{sTDEP}}`` | TI (MD) | TI (PIMD) | Cumulant |
|---|:---:|:---:|:---:|:---:|:---:|
| Quantum effects | ✓ | ✓ | | ✓ | ✓ |
| Renormalized IFCs | | ✓ | ✓ | ✓ | ✓ |
| No explicit dynamics | ✓ | ✓ | | | ✓ |
| Direct ``\mathcal{S}``, ``\mathcal{U}``, ``C_V`` | ✓ | | | | ✓ |
| Cubic/quartic anharmonicity | | | | | ✓ |
| Full anharmonicity | | | ✓ | ✓ | |

The cumulant approach trades TI's sampling-based error control for a truncated expansion around a self-consistent harmonic reference—valuable when multiple thermodynamic properties are needed efficiently, especially with quantum effects.

## Definitions of ``V_0``, ``\mathcal{F}_\mathrm{H}``, ``\mathcal{F}_1``, and ``\mathcal{F}_2``

### Reference energy ``V_0``

For a Taylor effective potential truncated beyond fourth order, the reference energy used in this work is

```math
V_0 \equiv \left\langle V - V_2 - V_3 - V_4 \right\rangle_\mathrm{H},
```

the harmonic ensemble average of all terms omitted from the Taylor expansion. In the code, configurations are drawn from the harmonic distribution at temperature ``T``; the true potential ``V`` is evaluated with LAMMPS and ``V_2``, ``V_3``, ``V_4`` from the IFCs. The sample mean estimates ``V_0``. Bootstrap resampling (`nboot`) provides a standard error on the 0th-order contribution.

With sTDEP IFCs, ``V_0`` is temperature dependent, which complicates analytical thermodynamic derivatives. The package addresses this with the sampling estimators described below.

### Harmonic term ``\mathcal{F}_\mathrm{H}``

Computed from the renormalized second-order IFCs via phonon dispersion and Brillouin-zone integration (`harmonic_q_mesh`). Supports quantum (`quantum = true`) or classical statistics.

### First cumulant ``\mathcal{F}_1``

When ``V \approx V_0 + V_2 + V_3 + V_4``, ``\mathcal{F}_1`` can be evaluated exactly as a sum over the irreducible Brillouin zone:

```math
\mathcal{F}_1 = \frac{\hbar^2}{8N}\sum_{\mathbf{k}\mathbf{k}'\lambda\lambda'}
\frac{\Phi_{\lambda\lambda'\lambda'\lambda'}^{\mathbf{k},-\mathbf{k},\mathbf{k}',-\mathbf{k}'}}{\omega_{\mathbf{k}\lambda}\,\omega_{\mathbf{k}'\lambda'}}
\left(n_{\mathbf{k}\lambda}+\frac{1}{2}\right)\left(n_{\mathbf{k}'\lambda'}+\frac{1}{2}\right),
```

where ``\Phi`` is the quartic mode-coupling tensor and ``n_{\mathbf{k}\lambda} = (e^{\beta\hbar\omega_{\mathbf{k}\lambda}}-1)^{-1}`` is the Bose–Einstein occupation. In CrystalCumulants.jl, ``\mathcal{F}_1`` is computed analytically by `free_energy_corrections` in LatticeDynamicsToolkit.jl (`free_energy_q_mesh`).

### Second cumulant ``\mathcal{F}_2``

Similarly,

```math
\begin{aligned}
\mathcal{F}_2 = -\frac{\hbar^2}{48N}
\sum_{\substack{\mathbf{k}\mathbf{k}'\mathbf{k}'' \\ \lambda\lambda'\lambda''}}
&\frac{\left|\Phi_{\lambda\lambda'\lambda''}^{\mathbf{k},\mathbf{k}',\mathbf{k}''}\right|^2}
{\omega_{\mathbf{k}\lambda}\,\omega_{\mathbf{k}'\lambda'}\,\omega_{\mathbf{k}''\lambda''}}
\Bigg[
\frac{(n_{\mathbf{k}\lambda}+1)(n_{\mathbf{k}'\lambda'}+n_{\mathbf{k}''\lambda''}+1) + n_{\mathbf{k}'\lambda'}n_{\mathbf{k}''\lambda''}}
{\omega_{\mathbf{k}\lambda}+\omega_{\mathbf{k}'\lambda'}+\omega_{\mathbf{k}''\lambda''}} \\
&+ 3\frac{n_{\mathbf{k}''\lambda''}(n_{\mathbf{k}\lambda}+n_{\mathbf{k}'\lambda'}+1)-n_{\mathbf{k}\lambda}n_{\mathbf{k}'\lambda'}}
{\omega_{\mathbf{k}\lambda}+\omega_{\mathbf{k}'\lambda'}-\omega_{\mathbf{k}''\lambda''}}
\Bigg],
\end{aligned}
```

where ``\Phi_{\lambda\lambda'\lambda''}^{\mathbf{k},\mathbf{k}',\mathbf{k}''}`` is the cubic mode-coupling tensor. This term is also evaluated analytically over the Brillouin zone in LatticeDynamicsToolkit.jl.

## Temperature derivatives of ``V_0``

Because ``V_0`` depends on temperature through the harmonic ensemble (and, approximately, through temperature-dependent IFCs), ``\mathcal{S}``, ``\mathcal{U}``, and ``C_V`` require ``\partial V_0 / \partial T`` and ``\partial^2 V_0 / \partial T^2``.

### Derivative of a harmonic expectation

For a quantity ``A`` depending only on atomic positions, the temperature derivative of ``\langle A \rangle_\mathrm{H}`` is

```math
\frac{\partial \langle A \rangle_\mathrm{H}}{\partial T}
=
\frac{\mathrm{cov}_\mathrm{H}\!\left(A,\,\widetilde{V}_2\right)}{k_\mathrm{B} T^2},
```

where ``\widetilde{V}_2`` is a mode-weighted harmonic energy:

```math
\widetilde{V}_2 = \frac{1}{2}\sum_{\mathbf{k}\lambda}
\frac{4\,n_{\mathbf{k}\lambda}\,\big(n_{\mathbf{k}\lambda}+1\big)}
{\big(2n_{\mathbf{k}\lambda}+1\big)^2}\,
\omega_{\mathbf{k}\lambda}^2\, q_{\mathbf{k}\lambda}^2,
```

with ``q_{\mathbf{k}\lambda}`` the mass-normalized normal-mode amplitude. In the classical limit, ``\widetilde{V}_2 = V_2``. The code uses ``\widetilde{V}_2`` for quantum calculations and ``V_2`` for classical ones (`V_ref` in `estimate.jl`).

### Entropy, internal energy, and heat capacity from ``V_0``

Define ``Y \equiv V - V_2 - V_3 - V_4``. The entropy contribution from ``V_0`` is estimated as

```math
\mathcal{S}_0 = -\frac{\partial V_0}{\partial T}
\approx -\frac{\mathrm{cov}_\mathrm{H}\!\left(Y,\,\widetilde{V}_2\right)}{k_\mathrm{B} T^2}.
```

Because ``V_2``, ``V_3``, and ``V_4`` are themselves temperature dependent (self-consistent IFCs), this is an approximation. The error is mitigated by the envelope theorem: sTDEP IFCs minimize ``\mathcal{F}^{\,\mathrm{sTDEP}}`` and do not contribute to the temperature derivative at leading order.

The internal energy contribution is

```math
\mathcal{U}_0 = V_0 + T\mathcal{S}_0.
```

For heat capacity, define ``W \equiv \mathrm{cov}_\mathrm{H}(Y,\,\widetilde{V}_2)``. Then

```math
C_{V,0} = -T\frac{\partial^2 V_0}{\partial T^2}
= \frac{2W}{k_\mathrm{B} T^2}
- \frac{1}{k_\mathrm{B}}\frac{\partial W}{\partial T},
```

and applying the covariance derivative formula to ``W`` gives

```math
\begin{aligned}
C_{V,0} =
&\frac{2\,\mathrm{cov}_\mathrm{H}(Y,\,\widetilde{V}_2)}{k_\mathrm{B} T^2}
-\frac{1}{k_\mathrm{B}^2 T^3}
\Big[
\mathrm{cov}_\mathrm{H}\!\left(Y\widetilde{V}_2,\,\widetilde{V}_2\right)
- \langle \widetilde{V}_2 \rangle_\mathrm{H}\,\mathrm{cov}_\mathrm{H}(Y,\,\widetilde{V}_2) \\
&\qquad\qquad\qquad\qquad\qquad
- \langle Y \rangle_\mathrm{H}\,\mathrm{cov}_\mathrm{H}(\widetilde{V}_2,\,\widetilde{V}_2)
\Big].
\end{aligned}
```

``C_{V,0}`` is expected to be less accurate than ``\mathcal{S}_0`` because it involves a second temperature derivative. These estimators are implemented in `cumulant_corrections.jl` via sample covariances over harmonic configurations (`nconf` samples; `nboot` for error bars on ``V_0`` and ``\mathcal{S}_0``).

In the output files, the 0th-order row is labeled `_offset` (corresponding to ``V_0`` and its derivatives); only this term includes bootstrap standard errors.

## Temperature derivatives of ``\mathcal{F}_1`` and ``\mathcal{F}_2``

Contributions to ``\mathcal{S}``, ``\mathcal{U}``, and ``C_V`` from ``\mathcal{F}_1`` and ``\mathcal{F}_2`` are obtained by **analytical differentiation** following

```math
\mathcal{S} = -\frac{\partial\mathcal{F}}{\partial T}, \qquad
\mathcal{U} = \frac{\partial(\beta\mathcal{F})}{\partial\beta}, \qquad
C_V = -T\frac{\partial^2\mathcal{F}}{\partial T^2}.
```

In these derivatives, phonon occupations ``n_{\mathbf{k}\lambda}`` are treated as temperature dependent; phonon frequencies ``\omega_{\mathbf{k}\lambda}`` do not contribute ``\partial\omega/\partial T`` terms (envelope theorem). Temperature derivatives of the mode-coupling tensors are neglected.

In the package, analytical ``\mathcal{F}_1`` and ``\mathcal{F}_2`` corrections (and their thermodynamic derivatives) are computed by `free_energy_corrections` in LatticeDynamicsToolkit.jl and combined with the harmonic baseline and sampled ``V_0`` terms in `bootstrap_corrections`.

## Total thermodynamic properties

The full vibrational properties are assembled as

```math
\mathcal{F} = \mathcal{F}_\mathrm{H} + V_0 + \mathcal{F}_1 + \mathcal{F}_2 + \cdots
```

(with corresponding sums for ``\mathcal{S}``, ``\mathcal{U}``, and ``C_V``). Output files (`F_mean.txt`, etc.) report each contribution separately: harmonic (`F0`), 0th-order offset, 1st-order (`F1`), 2nd-order (`F2`), and total.


## Limitations

- **Polar interactions** are not included in the current implementation, even if present in `infile.forceconstant`.
- **Self-consistent phonons** (sTDEP/SSCHA) are recommended; MD-TDEP or finite-difference IFCs reduce accuracy.
- **Truncation** at second cumulant order neglects higher anharmonicity captured only by full TI.
- **``V_0`` derivatives** are approximate when IFCs are temperature dependent; ``C_{V,0}`` is the most sensitive.
- **Mode-coupling temperature dependence** in ``\mathcal{F}_1`` and ``\mathcal{F}_2`` derivatives is neglected.

## Further reading

See the [Example](@ref Example) page for a worked walkthrough and the [Home](index.md) page for convergence settings (`nconf`, `free_energy_q_mesh`, `size_study`).
