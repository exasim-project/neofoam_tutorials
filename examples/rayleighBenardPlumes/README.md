# rayleighBenardPlumes: thermal plumes in Rayleigh-Benard convection at Ra = 1e11

A 2D square cell (H = L = 1 m) heated from below and cooled from above (floor 300.5 K,
ceiling 299.5 K, adiabatic side walls), Boussinesq, Ra = g beta dT H^3 / (nu kappa) = 1e11,
Pr = 1. The thermal boundary layers on the plates detach as hot and cold plumes, which
organise into a large-scale circulation of the cell.

| quantity | value |
|---|---|
| g, beta, dT | 9.81 m/s^2, 1/300 1/K, 1 K |
| nu = kappa | 5.7184e-7 m^2/s |
| free-fall velocity, time | sqrt(g beta dT H) = 0.181 m/s, 5.53 s |
| mesh | 128 x 128, graded 8:1 to the walls: 2.3 mm at the plates, 18.6 mm in the core |
| time | 300 s (about 54 free-fall times) in steps of 0.02 s, written every 10 s |
| start | at rest, T = 300 K plus 1 % of dT of noise (`setExprFields`) |

**This is a demo, not a resolved simulation.** At Ra = 1e11 the thermal boundary layers are
about H / (2 Nu) = 1.6 mm thick (Nu ~ 0.124 Ra^0.309 = 310, Niemela et al., Nature 2000), so
a resolved run needs a 3D mesh with billions of cells. Here the run is laminar on a
mesh that does not resolve them: it shows the plumes and the circulation, and its Nusselt
number is a rough estimate from the wall-adjacent cells.

## Running

```sh
source <OpenFOAM v2406>/etc/bashrc     # and NeoFOAM's Python environment active
./Allrun                               # neofoam solver incompressiblefluidneon, Serial
./Allrun incompressibleFluidNeoN GPU   # on the GPU (a CUDA build of NeoFOAM); also CPU
./Allrun incompressibleFluid           # neofoam solver incompressiblefluid (pybFoam)
./Allclean
```

`p_rgh` is solved by CG with an algebraic multigrid preconditioner, `system/amg.json`: NeoN's
MergedPgm aggregation with the GAMG scale correction, unsorted, smoothed by 3 sweeps of
Jacobi relaxed by 0.8. Tuned on the first 25 steps (Serial): 19 iterations per solve on average
(20 at most) against 84 (209) of 2 sweeps relaxed by 0.9, 0.19 s per step.
`incompressibleFluid` (pybFoam) has no Ginkgo; for it, set `p_rgh` to `GAMG` in
`system/fvSolution`.

NeoN allocates its fields from an Umpire memory pool (`allocator UmpirePool;
memPoolSize 1;` in `system/controlDict`, the first block in GB; the pool grows): on the GPU
the 250 steps of the first 5 s take 5.9 s instead of 9.1 s with the default allocator.

Both solvers detect the Boussinesq model from `beta` and `TRef` in
`constant/transportProperties`. For a quick check, shorten `endTime` in
`system/controlDict`. `plot.py` writes `plots/temperature.png` (T at the last written time)
and `plots/nusselt.png` (the plates' Nusselt numbers over time against Niemela et al.'s fit).
