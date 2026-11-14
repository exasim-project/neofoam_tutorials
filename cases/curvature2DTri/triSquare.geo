// TwoPhaseFlow curvature2DTri/triSquare.geo with nx = 33 (32 edges per side):
// unstructured triangles in the 2 x 2 x-z square, extruded by one prism layer.
// triSquare.msh is generated from it (gmsh 4.15.2):
//   gmsh -3 -format msh2 triSquare.geo
nx=33;

Point(1) = {-0, -0.05, 0, 1e+22};
Point(2) = {2, -0.05, 0, 1e+22};
Point(3) = {2, -0.05, 2, 1e+22};
Point(4) = {0, -0.05, 2, 1e+22};
Line(1) = {1, 2};
Line(2) = {2, 3};
Line(3) = {3, 4};
Line(4) = {4, 1};
Line Loop(6) = {4, 1, 2, 3};

Plane Surface(6) = {6};
Physical Volume("internal") = {1};

Transfinite Line{1} = nx;
Transfinite Line{2} = nx;
Transfinite Line{3} = nx;
Transfinite Line{4} = nx;

Extrude {0, 0.1, 0} {
  Surface{6};
  Layers{1};
  Recombine;
}

Physical Surface("back") = {6};
Physical Surface("rim") = {27, 15, 19, 23};
Physical Surface("front") = {28};
