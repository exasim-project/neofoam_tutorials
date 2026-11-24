/*---------------------------------------------------------------------------*\
License
    This file is not part of OpenFOAM.

    OpenFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

Application
    advectionFluxReference

Description
    Reference data of one isoAdvection::advect step (OpenFOAM-v2406
    geometricVoF) on a prescribed velocity, at the level of the face fluxes.

    alpha1 is set as in reconstructionReference (cutCellIso of the implicit
    function of system/initAlphaFieldDict). For every velocity of
    system/advectionFluxReferenceDict (U = U(C) in the cells, U(Cf) on the
    boundary faces, phi = U(Cf) & Sf), every Courant number Co
    (dt = Co/(0.5 max_cells sum_faces |phi|/V)) and every scheme:

    1. the library's isoAdvection on alpha "alpha.<scheme>.unbounded"
       (fvSolution: nAlphaBounds 0, clip off): its dVf_ is the face flux of
       timeIntegratedFlux() before bounding, its alpha the unbounded update;
    2. the library's isoAdvection on alpha "alpha.<scheme>" (nAlphaBounds 3,
       clip on, as interIsoFoam): its dVf_ after limitFluxes, alphaPhi and
       alpha after advect;
    3. a replay of isoAdvection::timeIntegratedFlux() with the interface of 2.
       that records, for every downwind face of every surface cell, the
       inputs of cutFaceAdvect::timeIntegratedFaceFlux and the intermediate
       values of cutFaceAdvectTrace (a copy of cutFaceAdvect). The utility
       stops unless the trace returns bitwise the library cutFaceAdvect's
       value on every face and the replayed dVf field equals 1.'s bitwise.

    Output (text tables, 17 significant digits) in advectionFluxReference/,
    converted to .npz by neofoam_tutorials.advection_flux, which documents
    the columns. Values on faces of empty patches are written as nan.

\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
#include "OFstream.H"
#include "emptyPolyPatch.H"
#include "implicitFunction.H"
#include "cutCellIso.H"
#include "isoAdvection.H"
#include "cutFaceAdvect.H"
#include "cutFaceAdvectTrace.H"
#include "interpolationCellPoint.H"
#include "volPointInterpolation.H"
#include "upwind.H"
#include "zeroField.H"

// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

namespace
{

using namespace Foam;

void writeVector(Ostream& os, const vector& v)
{
    os << token::SPACE << v.x() << token::SPACE << v.y() << token::SPACE << v.z();
}


//- The prescribed velocity at x: "uniform" (value) or "rotation"
//  (omega*normalised(axis) ^ (x - origin))
vector velocity(const dictionary& spec, const point& x)
{
    const word type(spec.get<word>("type"));
    if (type == "uniform")
    {
        return spec.get<vector>("value");
    }
    if (type == "rotation")
    {
        const vector axis(normalised(spec.get<vector>("axis")));
        return
            spec.get<scalar>("omega")
           *(axis ^ (x - spec.get<point>("origin")));
    }
    FatalErrorInFunction
        << "Unknown velocity type " << type << exit(FatalError);
    return Zero;
}


bool isEmptyFace(const fvMesh& mesh, const label facei)
{
    if (mesh.isInternalFace(facei))
    {
        return false;
    }
    const polyBoundaryMesh& pbm = mesh.boundaryMesh();
    return isA<emptyPolyPatch>(pbm[pbm.whichPatch(facei)]);
}


//- Value of a surface field on mesh face facei (nan on empty patches)
template<class Type>
Type faceValue
(
    const GeometricField<Type, fvsPatchField, surfaceMesh>& f,
    const label facei
)
{
    const fvMesh& mesh = f.mesh();
    if (mesh.isInternalFace(facei))
    {
        return f.primitiveField()[facei];
    }
    const polyBoundaryMesh& pbm = mesh.boundaryMesh();
    const label patchi = pbm.whichPatch(facei);
    const fvsPatchField<Type>& pf = f.boundaryField()[patchi];
    if (pf.empty())
    {
        return pTraits<Type>::one*NAN;
    }
    return pf[pbm[patchi].whichFace(facei)];
}


//- true if a and b differ (bitwise for numbers; nan equals nan)
bool differ(const scalar a, const scalar b)
{
    return a != b && !(std::isnan(a) && std::isnan(b));
}


//- One isoAdvection::advect step of the library on a copy of alpha0 named
//  name; returns dVf_ after advect and sets alpha (and alphaPhi if given)
surfaceScalarField advectLibrary
(
    const word& name,
    const volScalarField& alpha0,
    const surfaceScalarField& phi,
    const volVectorField& U,
    scalarField& alpha,
    surfaceScalarField* alphaPhi = nullptr
)
{
    volScalarField alpha1
    (
        IOobject(name, alpha0.time().timeName(), alpha0.mesh()),
        alpha0
    );
    isoAdvection advector(alpha1, phi, U);
    advector.advect(zeroField(), zeroField());
    alpha = alpha1.primitiveField();
    if (alphaPhi)
    {
        *alphaPhi = advector.alphaPhi();
    }
    return surfaceScalarField
    (
        "dVf." + name,
        alpha0.mesh().lookupObject<surfaceScalarField>("dVf_")
    );
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
            "advectionFluxReferenceDict",
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

    // alpha1 from the implicit function's point values (as
    // reconstructionReference and setAlphaField)
    {
        autoPtr<implicitFunction> func = implicitFunction::New
        (
            initAlphaFieldDict.get<word>("type"),
            initAlphaFieldDict
        );
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

    const polyBoundaryMesh& pbm = mesh.boundaryMesh();
    const labelList& own = mesh.faceOwner();
    const cellList& cellFaces = mesh.cells();

    const fileName outDir(runTime.path()/"advectionFluxReference");
    mkDir(outDir);

    {
        OFstream os(outDir/"faces.dat");
        os.precision(17);
        os  << "# patch empty magSf" << nl;
        for (label facei = 0; facei < mesh.nFaces(); ++facei)
        {
            os  << (mesh.isInternalFace(facei) ? -1 : pbm.whichPatch(facei))
                << token::SPACE << label(isEmptyFace(mesh, facei))
                << token::SPACE << faceValue(mesh.magSf(), facei) << nl;
        }
    }

    const wordList schemes(referenceDict.get<wordList>("schemes"));
    const scalarList courantNumbers
    (
        referenceDict.get<scalarList>("courantNumbers")
    );
    const dictionary& velocities = referenceDict.subDict("velocities");

    for (const word& velocityName : velocities.toc())
    {
        const dictionary& spec = velocities.subDict(velocityName);

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
        forAll(U, celli)
        {
            U[celli] = velocity(spec, mesh.C()[celli]);
        }
        forAll(phi, facei)
        {
            phi[facei] =
                velocity(spec, mesh.Cf()[facei]) & mesh.Sf()[facei];
        }
        forAll(pbm, patchi)
        {
            fvPatchVectorField& Up = U.boundaryFieldRef()[patchi];
            fvsPatchScalarField& phip = phi.boundaryFieldRef()[patchi];
            const fvsPatchVectorField& Cfp = mesh.Cf().boundaryField()[patchi];
            const fvsPatchVectorField& Sfp = mesh.Sf().boundaryField()[patchi];
            forAll(Up, i)
            {
                Up[i] = velocity(spec, Cfp[i]);
                phip[i] = Up[i] & Sfp[i];
            }
        }

        // OpenFOAM's CourantNo: 0.5*gMax(sumPhi/V)*dt
        const scalar rate =
            gMax
            (
                fvc::surfaceSum(mag(phi))().primitiveField()
               /mesh.V().field()
            );

        // the cell-point interpolated velocity (used for Un0)
        const pointVectorField Up
        (
            volPointInterpolation::New(mesh).interpolate(U)
        );

        forAll(courantNumbers, coi)
        {
            const scalar Co = courantNumbers[coi];
            runTime.setDeltaT(Co/(0.5*rate), false);
            const scalar dt = runTime.deltaTValue();
            const scalar maxCo = 0.5*rate*dt;

            Info<< "Velocity " << velocityName << ", Co " << Co
                << ", dt " << dt << endl;

            for (const word& scheme : schemes)
            {
                Info<< "    Scheme " << scheme << endl;

                const fileName dir
                (
                    outDir/velocityName/("Co" + Foam::name(coi))/scheme
                );
                mkDir(dir);

                // 1. the library, unbounded: dVf of timeIntegratedFlux()
                scalarField alphaUnbounded;
                const surfaceScalarField dVfUnbounded
                (
                    advectLibrary
                    (
                        "alpha." + scheme + ".unbounded",
                        alpha1, phi, U, alphaUnbounded
                    )
                );

                // 2. the library, bounded (interIsoFoam's settings)
                volScalarField alpha
                (
                    IOobject
                    (
                        "alpha." + scheme,
                        runTime.timeName(),
                        mesh
                    ),
                    alpha1
                );
                isoAdvection advector(alpha, phi, U);
                advector.advect(zeroField(), zeroField());
                const surfaceScalarField& dVfLimited =
                    mesh.lookupObject<surfaceScalarField>("dVf_");
                const reconstructionSchemes& surf = advector.surf();

                // 3. replay of isoAdvection::timeIntegratedFlux() on the
                // interface that advect() reconstructed
                const surfaceScalarField dVfUpwind
                (
                    "dVfUpwind",
                    upwind<scalar>(mesh, phi).flux(alpha1)*runTime.deltaT()
                );
                surfaceScalarField dVf("dVf", dVfUpwind);
                scalarField& dVfIn = dVf.primitiveFieldRef();
                surfaceScalarField::Boundary& dVfb = dVf.boundaryFieldRef();
                const scalarField& phiIn = phi.primitiveField();
                const scalarField& magSfIn = mesh.magSf().primitiveField();

                interpolationCellPoint<vector> UInterp(U);
                cutFaceAdvect advectFace(mesh, alpha1);
                cutFaceAdvectTrace traceFace(mesh, alpha1);

                OFstream interfaceOs(dir/"interface.dat");
                OFstream fluxOs(dir/"flux.dat");
                OFstream pTimesOs(dir/"pTimes.dat");
                OFstream stepsOs(dir/"steps.dat");
                for (OFstream* os : {&interfaceOs, &fluxOs, &pTimesOs, &stepsOs})
                {
                    os->precision(17);
                }
                interfaceOs << "# cell nx ny nz cx cy cz n0x n0y n0z Un0" << nl;
                fluxOs
                    << "# row cell interface face boundary x0x x0y x0z"
                    << " n0x n0y n0z Un0 dt phi magSf branch nShifts nPoints"
                    << " dVf area alphaf" << nl;
                pTimesOs << "# row pTimes..." << nl;
                stepsOs << "# row kind t0 t1 area0 alpha beta contribution" << nl;

                label row = 0;
                auto evaluate = [&]
                (
                    const label celli,
                    const label interfacei,
                    const label facei,
                    const point& x0,
                    const vector& n0,
                    const scalar Un0,
                    const scalar phif,
                    const scalar magSf
                ) -> scalar
                {
                    const scalar dVfLib = advectFace.timeIntegratedFaceFlux
                    (
                        facei, x0, n0, Un0, dt, phif, magSf
                    );
                    const scalar dVfTrace = traceFace.timeIntegratedFaceFlux
                    (
                        facei, x0, n0, Un0, dt, phif, magSf
                    );
                    if (differ(dVfLib, dVfTrace))
                    {
                        FatalErrorInFunction
                            << "cutFaceAdvectTrace differs from cutFaceAdvect"
                            << " on face " << facei << ": " << dVfTrace
                            << " != " << dVfLib << exit(FatalError);
                    }

                    fluxOs
                        << row << token::SPACE << celli
                        << token::SPACE << interfacei
                        << token::SPACE << facei
                        << token::SPACE << label(!mesh.isInternalFace(facei));
                    writeVector(fluxOs, x0);
                    writeVector(fluxOs, n0);
                    fluxOs
                        << token::SPACE << Un0 << token::SPACE << dt
                        << token::SPACE << phif << token::SPACE << magSf
                        << token::SPACE << traceFace.traceBranch()
                        << token::SPACE << traceFace.traceShifts()
                        << token::SPACE << mesh.faces()[facei].size()
                        << token::SPACE << dVfLib
                        << token::SPACE << traceFace.traceArea()
                        << token::SPACE << traceFace.traceAlphaf() << nl;

                    if (traceFace.pTimes().size())
                    {
                        pTimesOs << row;
                        for (const scalar t : traceFace.pTimes())
                        {
                            pTimesOs << token::SPACE << t;
                        }
                        pTimesOs << nl;
                    }
                    for (const FixedList<scalar, 7>& step : traceFace.traceSteps())
                    {
                        stepsOs << row;
                        for (const scalar v : step)
                        {
                            stepsOs << token::SPACE << v;
                        }
                        stepsOs << nl;
                    }
                    ++row;
                    return dVfLib;
                };

                const DynamicField<label>& interfaceLabels =
                    surf.interfaceLabels();

                scalarField Un0(interfaceLabels.size());
                forAll(Un0, i)
                {
                    const label celli = interfaceLabels[i];
                    const point x0(surf.centre()[celli]);
                    const vector n0(normalised(-surf.normal()[celli]));
                    Un0[i] = UInterp.interpolate(x0, celli) & n0;
                }

                // boundary faces of surface cells: face, interface index, i
                DynamicList<FixedList<label, 3>> bsFaces;
                label nSurfaceCells = 0;
                forAll(interfaceLabels, i)
                {
                    const label celli = interfaceLabels[i];
                    if (mag(surf.normal()[celli]) == 0)
                    {
                        continue;
                    }
                    const label interfacei = nSurfaceCells++;
                    const point x0(surf.centre()[celli]);
                    const vector n0(normalised(-surf.normal()[celli]));

                    interfaceOs << celli;
                    writeVector(interfaceOs, surf.normal()[celli]);
                    writeVector(interfaceOs, x0);
                    writeVector(interfaceOs, n0);
                    interfaceOs << token::SPACE << Un0[i] << nl;

                    for (const label facei : cellFaces[celli])
                    {
                        if (mesh.isInternalFace(facei))
                        {
                            const bool isDownwindFace =
                                celli == own[facei]
                              ? phiIn[facei] >= 0
                              : phiIn[facei] < 0;
                            if (isDownwindFace)
                            {
                                dVfIn[facei] = evaluate
                                (
                                    celli, interfacei, facei, x0, n0, Un0[i],
                                    phiIn[facei], magSfIn[facei]
                                );
                            }
                        }
                        else
                        {
                            bsFaces.append(FixedList<label, 3>({facei, interfacei, i}));
                        }
                    }
                }
                for (const FixedList<label, 3>& bs : bsFaces)
                {
                    const label facei = bs[0];
                    const label celli = interfaceLabels[bs[2]];
                    const label patchi = pbm.whichPatch(facei);
                    if (!phi.boundaryField()[patchi].empty())
                    {
                        const label patchFacei = pbm[patchi].whichFace(facei);
                        const scalar phiP = phi.boundaryField()[patchi][patchFacei];
                        if (phiP >= 0)
                        {
                            dVfb[patchi][patchFacei] = evaluate
                            (
                                celli, bs[1], facei,
                                surf.centre()[celli],
                                normalised(-surf.normal()[celli]),
                                Un0[bs[2]], phiP,
                                mesh.magSf().boundaryField()[patchi][patchFacei]
                            );
                        }
                    }
                }

                for (label facei = 0; facei < mesh.nFaces(); ++facei)
                {
                    if
                    (
                        differ
                        (
                            faceValue(dVf, facei),
                            faceValue(dVfUnbounded, facei)
                        )
                    )
                    {
                        FatalErrorInFunction
                            << "The replayed dVf differs from isoAdvection's"
                            << " on face " << facei << ": "
                            << faceValue(dVf, facei) << " != "
                            << faceValue(dVfUnbounded, facei)
                            << exit(FatalError);
                    }
                }

                {
                    OFstream os(dir/"faces.dat");
                    os.precision(17);
                    os  << "# phi Ux Uy Uz dVfUpwind dVf dVfLimited alphaPhi"
                        << nl;
                    for (label facei = 0; facei < mesh.nFaces(); ++facei)
                    {
                        os  << faceValue(phi, facei);
                        // U on boundary faces (nan on internal faces)
                        vector Uf(pTraits<vector>::one*NAN);
                        if (!mesh.isInternalFace(facei))
                        {
                            const label patchi = pbm.whichPatch(facei);
                            const fvPatchVectorField& Ub =
                                U.boundaryField()[patchi];
                            if (Ub.size())
                            {
                                Uf = Ub[pbm[patchi].whichFace(facei)];
                            }
                        }
                        writeVector(os, Uf);
                        os  << token::SPACE << faceValue(dVfUpwind, facei)
                            << token::SPACE << faceValue(dVf, facei)
                            << token::SPACE << faceValue(dVfLimited, facei)
                            << token::SPACE
                            << faceValue(advector.alphaPhi(), facei) << nl;
                    }
                }
                {
                    OFstream os(dir/"cells.dat");
                    os.precision(17);
                    os  << "# Ux Uy Uz alpha0 alphaUnbounded alpha" << nl;
                    forAll(U, celli)
                    {
                        writeVector(os, U[celli]);
                        os  << token::SPACE << alpha1[celli]
                            << token::SPACE << alphaUnbounded[celli]
                            << token::SPACE << alpha[celli] << nl;
                    }
                }
                {
                    OFstream os(dir/"points.dat");
                    os.precision(17);
                    os  << "# Ux Uy Uz" << nl;
                    forAll(Up, pointi)
                    {
                        writeVector(os, Up[pointi]);
                        os  << nl;
                    }
                }
                {
                    OFstream os(dir/"run.dat");
                    os.precision(17);
                    os  << "# dt courant maxCourant" << nl
                        << dt << token::SPACE << Co << token::SPACE << maxCo
                        << nl;
                }

                Info<< "        surface cells " << nSurfaceCells
                    << ", traced faces " << row << endl;
            }
        }
    }

    Info<< "End\n" << endl;

    return 0;
}


// ************************************************************************* //
