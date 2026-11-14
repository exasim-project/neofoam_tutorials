// TwoPhaseFlow curvature3DTri/triBlock.geo with nx = 11 (10 edges per side), in the
// 2 x 2 x 2 cube of curvature3D (TwoPhaseFlow's block is the unit cube, which holds
// only an octant of the sphere): unstructured tetrahedra.
// triBlock.msh is generated from it (gmsh 4.15.2):
//   gmsh -3 -optimize_netgen -format msh2 triBlock.geo
nx=11;

SetFactory("OpenCASCADE");
Block(1) = {0, 0, 0, 2, 2, 2};
Transfinite Line {11, 9, 12, 10} = nx Using Progression 1;
Transfinite Line {7, 6, 5, 8, 3, 4, 1, 2} = nx Using Progression 1;
Physical Surface("rim") = {6, 2, 4, 3, 5, 1};
Physical Volume("internal") = {1};
