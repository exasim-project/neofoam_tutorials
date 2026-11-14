/*---------------------------------------------------------------------------*\
License
    This file is not part of OpenFOAM.

    OpenFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

Application
    reconstructionReference

Description
    Reference data of OpenFOAM's geometricVoF interface reconstruction on a
    known interface, after TwoPhaseFlow's apps/benchmark/reconstructInterface
    (nIter 1, fixed origin, no curvature):

    1. alpha1 = cutCellIso volume fraction of the implicit function of
       system/initAlphaFieldDict (as setAlphaField),
    2. for every scheme of system/reconstructionReferenceDict (one at a time):
       reconstruct(), then for every cell with a non-zero interface normal
       - the interface normal and centre,
       - cutCellPLIC::calcSubCell of a fixed set of planes,
       - surfaceIteratorPLIC::vofCutCell (the signed distance matching a
         target volume fraction) for a set of normals and targets,
       - TwoPhaseFlow's reconstructionError normal and centre errors,
       and for gradAlpha, for every interface cell (interfaceLabels), the
       least-squares gradient of gradAlpha::gradSurf (the normal handed to
       vofCutCell) and its zoneDistribute stencil; the utility stops unless
       vofCutCell with this gradient gives the scheme's normal and centre
       bitwise.

    Output (text tables, 17 significant digits) in reconstructionReference/,
    converted to .npz by neofoam_verification.reconstruction, which documents
    the columns.

    Planes per interface cell, with C the cell centre, n0 = normal/|normal|
    (the interface normal points into the fluid, alpha = 1; mapAlphaField's
    convention), x0 the interface centre, f(n) = (p - C) & n
    over the cell points p and r(n) = max f - min f:
        0  n0, cut value d0 = (x0 - C) & n0 (the reconstructed plane)
        1  n0, d0 - 0.25 r(n0)
        2  n0, d0 + 0.25 r(n0)
        3  n1 = n0 rotated by 20 deg about a1, through x0
        4  n2 = n0 rotated by 20 deg about a2, through x0
        5  n0, max f(n0) + 0.1 r(n0) (cell above the plane, alpha 0)
        6  n0, min f(n0) - 0.1 r(n0) (cell below the plane, alpha 1)
        7  normalised (1 2 3), through C
    a1 = normalised(n0 ^ e), e the coordinate axis least aligned with n0
    (ties in the order y, z, x, so that a2 = n0 ^ a1 is the y axis for an x-z
    normal of the 2D cases).

\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
#include "OFstream.H"
#include "unitConversion.H"
#include "implicitFunction.H"
#include "cutCellIso.H"
#include "cutCellPLIC.H"
#include "surfaceIteratorPLIC.H"
#include "reconstructionSchemes.H"
#include "zoneDistribute.H"
#include "leastSquareGrad.H"

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

namespace
{

using namespace Foam;

vector rotate(const vector& v, const vector& k, const scalar angle)
{
    return
        v*Foam::cos(angle)
      + (k ^ v)*Foam::sin(angle)
      + k*(k & v)*(1 - Foam::cos(angle));
}


void writeVector(Ostream& os, const vector& v)
{
    os << token::SPACE << v.x() << token::SPACE << v.y() << token::SPACE << v.z();
}


//- min and max of (p - C) & n over the cell points
Pair<scalar> extent(const fvMesh& mesh, const label celli, const vector& n)
{
    scalar fmin = GREAT;
    scalar fmax = -GREAT;
    for (const label pointi : mesh.cellPoints(celli))
    {
        const scalar f = (mesh.points()[pointi] - mesh.C()[celli]) & n;
        fmin = min(fmin, f);
        fmax = max(fmax, f);
    }
    return Pair<scalar>(fmin, fmax);
}


void writeCut(Ostream& os, const cutCellPLIC& cut)
{
    os  << token::SPACE << cut.cellStatus()
        << token::SPACE << cut.VolumeOfFluid()
        << token::SPACE << cut.subCellVolume();
    writeVector(os, cut.faceCentre());
    writeVector(os, cut.faceArea());
    writeVector(os, cut.subCellCentre());
}


//- gradAlpha::gradSurf replayed after reconstruct() (the stencil and maps of
//  its zoneDistribute, serial: global = local cell labels); per interface
//  cell: cell gx gy gz nStencil stencil...
void writeGradAlpha
(
    const fileName& file,
    const reconstructionSchemes& surf,
    const volScalarField& alpha1,
    const scalar isoFaceTol,
    const scalar surfCellTol
)
{
    const fvMesh& mesh = alpha1.mesh();
    leastSquareGrad<scalar> lsGrad("polyDegree1", mesh.geometricD());
    zoneDistribute& exchangeFields = zoneDistribute::New(mesh);
    const boolList interfaceCell(surf.interfaceCell());
    Map<vector> mapCC
    (
        exchangeFields.getDatafromOtherProc(interfaceCell, mesh.C())
    );
    Map<scalar> mapPhi
    (
        exchangeFields.getDatafromOtherProc(interfaceCell, alpha1)
    );
    const labelListList& stencil = exchangeFields.getStencil();
    surfaceIteratorPLIC sIter(mesh, surfCellTol);

    OFstream os(file);
    os.precision(17);
    os  << "# cell gx gy gz nStencil stencil..." << nl;

    DynamicField<vector> cellCentre(100);
    DynamicField<scalar> phiValues(100);
    for (const label celli : surf.interfaceLabels())
    {
        cellCentre.clear();
        phiValues.clear();
        for (const label gblIdx : stencil[celli])
        {
            cellCentre.append
            (
                exchangeFields.getValue(mesh.C(), mapCC, gblIdx)
            );
            phiValues.append
            (
                exchangeFields.getValue(alpha1, mapPhi, gblIdx)
            );
        }
        cellCentre -= mesh.C()[celli];
        const vector grad(lsGrad.grad(cellCentre, phiValues));

        os  << celli;
        writeVector(os, grad);
        os  << token::SPACE << stencil[celli].size();
        for (const label gblIdx : stencil[celli])
        {
            os  << token::SPACE << gblIdx;
        }
        os  << nl;

        // gradAlpha::reconstruct with this gradient
        vector n(Zero);
        vector c(Zero);
        if (mag(grad) != 0)
        {
            sIter.vofCutCell(celli, alpha1[celli], isoFaceTol, 100, grad);
            if (sIter.cellStatus() == 0)
            {
                n = sIter.surfaceArea();
                c = sIter.surfaceCentre();
                if (mag(n) == 0)
                {
                    c = Zero;
                }
            }
        }
        if (n != surf.normal()[celli] || c != surf.centre()[celli])
        {
            FatalErrorInFunction
                << "The replayed gradAlpha normal differs in cell " << celli
                << ": " << n << " != " << surf.normal()[celli]
                << exit(FatalError);
        }
    }
}

} // End namespace


int main(int argc, char *argv[])
{
    argList::noFunctionObjects();

    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"

    IOdictionary initAlphaFieldDict
    (
        IOobject
        (
            "initAlphaFieldDict",
            runTime.system(),
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        )
    );

    IOdictionary referenceDict
    (
        IOobject
        (
            "reconstructionReferenceDict",
            runTime.system(),
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        )
    );

    volScalarField alpha1
    (
        IOobject
        (
            "alpha1",
            runTime.timeName(),
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        ),
        mesh
    );

    volVectorField U
    (
        IOobject("U", runTime.timeName(), mesh),
        mesh,
        dimensionedVector(dimVelocity, Zero)
    );

    surfaceScalarField phi
    (
        IOobject("phi", runTime.timeName(), mesh),
        mesh,
        dimensionedScalar(dimVelocity*dimArea, Zero)
    );

    autoPtr<implicitFunction> func = implicitFunction::New
    (
        initAlphaFieldDict.get<word>("type"),
        initAlphaFieldDict
    );

    // 1. alpha1 from the implicit function's point values (setAlphaField)
    {
        scalarField f(mesh.nPoints());
        forAll(f, pointi)
        {
            f[pointi] = func->value(mesh.points()[pointi]);
        }
        cutCellIso cutCell(mesh, f);
        forAll(alpha1, celli)
        {
            cutCell.calcSubCell(celli, 0.0);
            alpha1[celli] = clamp(cutCell.VolumeOfFluid(), zero_one{});
        }
        alpha1.correctBoundaryConditions();
    }

    const fileName outDir(runTime.path()/"reconstructionReference");
    mkDir(outDir);

    {
        OFstream os(outDir/"cells.dat");
        os.precision(17);
        os  << "# alpha Cx Cy Cz V" << nl;
        forAll(alpha1, celli)
        {
            os  << alpha1[celli];
            writeVector(os, mesh.C()[celli]);
            os  << token::SPACE << mesh.V()[celli] << nl;
        }
    }

    const scalar tol = referenceDict.get<scalar>("vofCutCellTol");
    const label maxIter = referenceDict.get<label>("vofCutCellMaxIter");
    const scalarList targets(referenceDict.get<scalarList>("alphaTargets"));
    const scalar angle = degToRad(20.0);
    const vector fixedNormal(normalised(vector(1, 2, 3)));

    for (const word& schemeName : referenceDict.get<wordList>("schemes"))
    {
        Info<< "Scheme " << schemeName << endl;

        const dictionary& schemeDict = referenceDict.subDict(schemeName);
        autoPtr<reconstructionSchemes> surf =
            reconstructionSchemes::New(alpha1, phi, U, schemeDict);
        surf->reconstruct();

        const volVectorField& normal = surf->normal();
        const volVectorField& centre = surf->centre();

        const fileName schemeDir(outDir/schemeName);
        mkDir(schemeDir);

        if (schemeDict.get<word>("reconstructionScheme") == "gradAlpha")
        {
            writeGradAlpha
            (
                schemeDir/"gradient.dat",
                *surf,
                alpha1,
                schemeDict.getOrDefault<scalar>("isoFaceTol", 1e-8),
                schemeDict.getOrDefault<scalar>("surfCellTol", 1e-8)
            );
        }

        OFstream interfaceOs(schemeDir/"interface.dat");
        OFstream planesOs(schemeDir/"planes.dat");
        OFstream sdOs(schemeDir/"signedDistance.dat");
        for (OFstream* os : {&interfaceOs, &planesOs, &sdOs})
        {
            os->precision(17);
        }
        interfaceOs << "# cell nx ny nz cx cy cz" << nl;
        planesOs
            << "# cell plane nx ny nz cutValue status alpha subVolume"
            << " fcx fcy fcz fax fay faz scx scy scz" << nl;
        sdOs
            << "# cell k nx ny nz alphaTarget status cutValue alpha"
            << " subVolume fcx fcy fcz fax fay faz scx scy scz" << nl;

        cutCellPLIC cut(mesh);
        surfaceIteratorPLIC sIter(mesh, schemeDict.get<scalar>("surfCellTol"));

        DynamicList<scalar> LNormal;
        DynamicList<scalar> LCentre;

        forAll(normal, celli)
        {
            if (mag(normal[celli]) == 0)
            {
                continue;
            }
            const point& C = mesh.C()[celli];
            const point& x0 = centre[celli];
            const vector n0(normal[celli]/mag(normal[celli]));

            interfaceOs << celli;
            writeVector(interfaceOs, normal[celli]);
            writeVector(interfaceOs, x0);
            interfaceOs << nl;

            // reconstructionError (TwoPhaseFlow)
            const vector exactNormal(func->grad(x0));
            LNormal.append(1 - (n0 & exactNormal)/mag(exactNormal));
            LCentre.append(mag(func->distanceToSurfaces(x0)));

            // rotation axes
            vector e(0, 1, 0);
            scalar least = mag(n0.y());
            if (mag(n0.z()) < least)
            {
                e = vector(0, 0, 1);
                least = mag(n0.z());
            }
            if (mag(n0.x()) < least)
            {
                e = vector(1, 0, 0);
            }
            const vector a1(normalised(n0 ^ e));
            const vector a2(n0 ^ a1);
            const vector n1(rotate(n0, a1, angle));
            const vector n2(rotate(n0, a2, angle));

            const scalar d0 = (x0 - C) & n0;
            const Pair<scalar> f0 = extent(mesh, celli, n0);
            const scalar r0 = f0.second() - f0.first();

            const List<Tuple2<vector, scalar>> planes
            ({
                {n0, d0},
                {n0, d0 - 0.25*r0},
                {n0, d0 + 0.25*r0},
                {n1, (x0 - C) & n1},
                {n2, (x0 - C) & n2},
                {n0, f0.second() + 0.1*r0},
                {n0, f0.first() - 0.1*r0},
                {fixedNormal, 0}
            });

            forAll(planes, planei)
            {
                const vector& n = planes[planei].first();
                const scalar d = planes[planei].second();
                cut.calcSubCell(celli, d, n);
                planesOs << celli << token::SPACE << planei;
                writeVector(planesOs, n);
                planesOs << token::SPACE << d;
                writeCut(planesOs, cut);
                planesOs << nl;
            }

            // signed distance (vofCutCell) for the normals n0, n1, n2 and the
            // targets: the cell's alpha, then alphaTargets;
            // k = normal index*number of targets + target index
            scalarList cellTargets(1, alpha1[celli]);
            cellTargets.append(targets);
            const List<vector> sdNormals({n0, n1, n2});
            forAll(sdNormals, normali)
            {
                forAll(cellTargets, targeti)
                {
                    const scalar target = cellTargets[targeti];
                    const label status = sIter.vofCutCell
                    (
                        celli, target, tol, maxIter, sdNormals[normali]
                    );
                    sdOs<< celli << token::SPACE
                        << normali*cellTargets.size() + targeti;
                    writeVector(sdOs, sdNormals[normali]);
                    sdOs<< token::SPACE << target
                        << token::SPACE << status
                        << token::SPACE << sIter.cutValue()
                        << token::SPACE << sIter.VolumeOfFluid()
                        << token::SPACE << sIter.subCellVolume();
                    writeVector(sdOs, sIter.surfaceCentre());
                    writeVector(sdOs, sIter.surfaceArea());
                    writeVector(sdOs, sIter.subCellCentre());
                    sdOs << nl;
                }
            }
        }

        OFstream errorOs(schemeDir/"error.dat");
        errorOs.precision(17);
        errorOs
            << "# LNormalInf LNormal1 LCentreInf LCentre1 nInterfaceCells" << nl
            << max(LNormal) << token::SPACE << average(LNormal)
            << token::SPACE << max(LCentre) << token::SPACE << average(LCentre)
            << token::SPACE << LNormal.size() << nl;

        Info<< "    interface cells " << LNormal.size()
            << ", LNormalInf " << max(LNormal)
            << ", LCentreInf " << max(LCentre) << endl;
    }

    Info<< "End\n" << endl;

    return 0;
}


// ************************************************************************* //
