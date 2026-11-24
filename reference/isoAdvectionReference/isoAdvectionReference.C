/*---------------------------------------------------------------------------*\
License
    This file is not part of OpenFOAM.

    OpenFOAM is free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

Application
    isoAdvectionReference

Description
    Reference data of a multi-step isoAdvection run (OpenFOAM-v2406
    geometricVoF) on a prescribed velocity: the time loop of TwoPhaseFlow's
    advectorVoF (CourantNo, alphaCourantNo and its setDeltaT, the
    time-dependent phi and U of the isoAdvector dict of fvSolution) with
    interIsoFoam's advect(zeroField, zeroField).

    Alpha: -implicitFunction sets it from system/initAlphaFieldDict by
    cutCellIso (as reconstructionReference), else it is read from 0/<-alpha>.
    Velocity: -velocity <name> takes the uniform or rotation velocity of
    system/isoAdvectionReferenceDict (as advectionFluxReference), else 0/U
    and 0/phi are read (phi = flux(U) if absent, as createPhi).

    The advected field is alpha.<scheme>; fvSolution's solver dict of that
    name has nAlphaBounds 3 and clip false: the utility clips alpha to
    [0, 1] after advect itself (applyBruteForceBounding with clip and
    snapTol 0 is that clamp and correctBoundaryConditions), so alpha before
    the clipping is seen in every step. The number of limitFluxes
    iterations of a step is found with copies alpha.<scheme>.b<n> (solver
    dicts with nAlphaBounds n, clip false, n = 0, 1, 2) advected from the
    same old alpha: limitFluxes runs iteration n + 1 iff alpha after n
    iterations exceeds [-100 SMALL, 1 + 100 SMALL]. The utility stops
    unless the copy after the last iteration equals alpha.<scheme> bitwise,
    and in step 1 unless alpha.<scheme>.clip (nAlphaBounds 3, clip true)
    equals the clipped alpha.<scheme> bitwise.

    Output (text tables, 17 significant digits) in
    isoAdvectionReference/[<velocity>/]<scheme>/: steps.dat (one row per
    step), alpha/<step>.dat (alpha after the step, at step 1, every
    -alphaInterval steps and at the write times) and step1/ (the pieces of
    the first step), converted to .npz by neofoam_tutorials.isoadvection,
    which documents the columns. Values on faces of empty patches are nan.

\*---------------------------------------------------------------------------*/

#include "fvCFD.H"
#include "OFstream.H"
#include "emptyPolyPatch.H"
#include "implicitFunction.H"
#include "cutCellIso.H"
#include "isoAdvection.H"
#include "interpolationCellPoint.H"
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


//- Value of a surface field on mesh face facei (nan on empty patches)
scalar faceValue(const surfaceScalarField& f, const label facei)
{
    const fvMesh& mesh = f.mesh();
    if (mesh.isInternalFace(facei))
    {
        return f.primitiveField()[facei];
    }
    const polyBoundaryMesh& pbm = mesh.boundaryMesh();
    const label patchi = pbm.whichPatch(facei);
    const fvsPatchScalarField& pf = f.boundaryField()[patchi];
    if (pf.empty())
    {
        return NAN;
    }
    return pf[pbm[patchi].whichFace(facei)];
}


//- true if alpha leaves [-aTol, 1 + aTol] (limitFluxes' loop condition)
bool unbounded(const volScalarField& alpha)
{
    const scalar aTol = 100*SMALL;
    return gMax(alpha.primitiveField()) - 1 > aTol
        || gMin(alpha.primitiveField()) < -aTol;
}


//- One library advect of a copy of alpha (alpha's old time, the value
//  before the step) named name; returns the advected copy
tmp<volScalarField> advectCopy
(
    const word& name,
    const volScalarField& alpha,
    const surfaceScalarField& phi,
    const volVectorField& U,
    autoPtr<surfaceScalarField>* dVf = nullptr
)
{
    tmp<volScalarField> tcopy
    (
        new volScalarField
        (
            IOobject(name, alpha.time().timeName(), alpha.mesh()),
            alpha
        )
    );
    isoAdvection advector(tcopy.ref(), phi, U);
    advector.advect(zeroField(), zeroField());
    if (dVf)
    {
        // only registered (and found) if no other isoAdvection exists
        dVf->reset
        (
            new surfaceScalarField
            (
                "dVf." + name,
                alpha.mesh().lookupObject<surfaceScalarField>("dVf_")
            )
        );
    }
    return tcopy;
}


void checkEqual
(
    const scalarField& a,
    const scalarField& b,
    const string& what
)
{
    forAll(a, i)
    {
        if (a[i] != b[i])
        {
            FatalErrorInFunction
                << what << " differ in cell " << i << ": " << a[i]
                << " != " << b[i] << exit(FatalError);
        }
    }
}


void writeAlpha(const fileName& file, const scalarField& alpha)
{
    OFstream os(file);
    os.precision(17);
    for (const scalar a : alpha)
    {
        os << a << nl;
    }
}

} // End namespace


int main(int argc, char *argv[])
{
    argList::noFunctionObjects();
    argList::addOption("scheme", "word", "reconstruction scheme");
    argList::addOption
    (
        "alpha", "word", "initial alpha field in 0/ (default alpha.water)"
    );
    argList::addBoolOption
    (
        "implicitFunction",
        "set alpha from system/initAlphaFieldDict by cutCellIso"
    );
    argList::addOption
    (
        "velocity", "word",
        "velocity of system/isoAdvectionReferenceDict (default 0/U, 0/phi)"
    );
    argList::addOption
    (
        "alphaInterval", "label",
        "write alpha every N steps (default 1; 0: step 1 and write times only)"
    );

    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"
    #include "createTimeControls.H"

    const word scheme(args.get<word>("scheme"));
    const label alphaInterval(args.getOrDefault<label>("alphaInterval", 1));
    const word velocityName(args.getOrDefault<word>("velocity", ""));

    volScalarField alpha0
    (
        IOobject
        (
            args.getOrDefault<word>("alpha", "alpha.water"),
            runTime.timeName(),
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        ),
        mesh
    );

    if (args.found("implicitFunction"))
    {
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
        forAll(alpha0, celli)
        {
            cutCell.calcSubCell(celli, 0.0);
            alpha0[celli] = clamp(cutCell.VolumeOfFluid(), zero_one{});
        }
        alpha0.correctBoundaryConditions();
    }

    autoPtr<volVectorField> UPtr;
    autoPtr<surfaceScalarField> phiPtr;
    if (velocityName.size())
    {
        IOdictionary referenceDict
        (
            IOobject
            (
                "isoAdvectionReferenceDict",
                runTime.system(),
                mesh,
                IOobject::MUST_READ,
                IOobject::NO_WRITE
            )
        );
        const dictionary& spec =
            referenceDict.subDict("velocities").subDict(velocityName);

        UPtr.reset
        (
            new volVectorField
            (
                IOobject("U", runTime.timeName(), mesh),
                mesh,
                dimensionedVector(dimVelocity, Zero)
            )
        );
        phiPtr.reset
        (
            new surfaceScalarField
            (
                IOobject("phi", runTime.timeName(), mesh),
                mesh,
                dimensionedScalar(dimVelocity*dimArea, Zero)
            )
        );
        volVectorField& U = UPtr();
        surfaceScalarField& phi = phiPtr();
        forAll(U, celli)
        {
            U[celli] = velocity(spec, mesh.C()[celli]);
        }
        forAll(phi, facei)
        {
            phi[facei] = velocity(spec, mesh.Cf()[facei]) & mesh.Sf()[facei];
        }
        forAll(mesh.boundaryMesh(), patchi)
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
    }
    else
    {
        UPtr.reset
        (
            new volVectorField
            (
                IOobject
                (
                    "U",
                    runTime.timeName(),
                    mesh,
                    IOobject::MUST_READ,
                    IOobject::NO_WRITE
                ),
                mesh
            )
        );
        // as createPhi.H
        phiPtr.reset
        (
            new surfaceScalarField
            (
                IOobject
                (
                    "phi",
                    runTime.timeName(),
                    mesh,
                    IOobject::READ_IF_PRESENT,
                    IOobject::NO_WRITE
                ),
                fvc::flux(UPtr())
            )
        );
    }
    volVectorField& U = UPtr();
    surfaceScalarField& phi = phiPtr();

    // advectorVoF: copies of the initial U and phi for the periodic flows
    const surfaceScalarField phi0("phi0", phi);
    const volVectorField U0("U0", U);
    const dictionary& isoAdvectorDict =
        mesh.solutionDict().subOrEmptyDict("isoAdvector");
    const scalar period = isoAdvectorDict.getOrDefault<scalar>("period", 0);
    scalar reverseTime =
        isoAdvectorDict.getOrDefault<scalar>("reverseTime", 0);
    const scalar spirallingFlow =
        isoAdvectorDict.getOrDefault<scalar>("spirallingFlow", 0);
    if (reverseTime > 0)
    {
        FatalErrorInFunction
            << "reverseTime is not supported" << exit(FatalError);
    }

    volScalarField alpha1
    (
        IOobject("alpha." + scheme, runTime.timeName(), mesh),
        alpha0
    );

    const fileName outDir
    (
        runTime.path()/"isoAdvectionReference"
       /(velocityName.size() ? fileName(velocityName/scheme) : fileName(scheme))
    );
    mkDir(outDir/"alpha");
    mkDir(outDir/"step1");
    writeAlpha(outDir/"alpha"/"0.dat", alpha1.primitiveField());

    OFstream stepsOs(outDir/"steps.dat");
    stepsOs.precision(17);
    stepsOs
        << "# step t dt CoNum alphaCoNum nIter nSurfaceCells"
        << " massUnclipped minUnclipped maxUnclipped mass min max" << nl;

    // advectorVoF: the time step from CourantNo and alphaCourantNo
    scalar CoNum = 0;
    scalar alphaCoNum = 0;
    auto setDeltaT = [&]()
    {
        #include "readTimeControls.H"
        const scalar maxAlphaCo
        (
            runTime.controlDict().get<scalar>("maxAlphaCo")
        );
        const scalarField sumPhi
        (
            fvc::surfaceSum(mag(phi))().primitiveField()
        );
        CoNum = 0.5*gMax(sumPhi/mesh.V().field())*runTime.deltaTValue();
        alphaCoNum =
            0.5
           *gMax
            (
                pos(alpha1.primitiveField() - 0.01)
               *pos(0.99 - alpha1.primitiveField())
               *sumPhi/mesh.V().field()
            )
           *runTime.deltaTValue();
        if (adjustTimeStep)
        {
            const scalar maxDeltaTFact =
                min(maxCo/(CoNum + SMALL), maxAlphaCo/(alphaCoNum + SMALL));
            runTime.setDeltaT
            (
                min(maxDeltaTFact*runTime.deltaTValue(), maxDeltaT)
            );
        }
    };
    setDeltaT();

    autoPtr<isoAdvection> advector;
    label step = 0;
    while (runTime.run())
    {
        setDeltaT();
        {
            const scalar t = runTime.value();
            const scalar dt = runTime.deltaTValue();
            if (period > 0)
            {
                phi = phi0*Foam::cos(2.0*M_PI*(t + 0.5*dt)/period);
                U = U0*Foam::cos(2.0*M_PI*(t + 0.5*dt)/period);
            }
            if (spirallingFlow > 0)
            {
                U = U0*Foam::cos(constant::mathematical::pi*(t + 0.5*dt)/spirallingFlow);
                phi = phi0*Foam::cos(constant::mathematical::pi*(t + 0.5*dt)/spirallingFlow);
            }
        }

        runTime++;
        ++step;

        // the old alpha is stored before the copies are made
        alpha1.oldTime();

        // limitFluxes iterations: copies with nAlphaBounds 0, 1, 2
        label nIter = 0;
        tmp<volScalarField> tlast;
        autoPtr<surfaceScalarField> dVfUnlimited;
        List<scalarField> boundsStep1(3);
        for (; nIter < 3; ++nIter)
        {
            tlast = advectCopy
            (
                alpha1.name() + ".b" + Foam::name(nIter),
                alpha1, phi, U,
                (step == 1 && nIter == 0) ? &dVfUnlimited : nullptr
            );
            if (step == 1)
            {
                boundsStep1[nIter] = tlast().primitiveField();
            }
            if (!unbounded(tlast()))
            {
                break;
            }
        }
        tmp<volScalarField> tclipped;
        if (step == 1)
        {
            tclipped = advectCopy(alpha1.name() + ".clip", alpha1, phi, U);
            advector.reset(new isoAdvection(alpha1, phi, U));
        }

        advector->advect(zeroField(), zeroField());

        if (nIter < 3)
        {
            checkEqual
            (
                tlast().primitiveField(), alpha1.primitiveField(),
                "alpha after " + Foam::name(nIter) + " limitFluxes iterations"
            );
        }

        const scalarField& V = mesh.V().field();
        const scalar massUnclipped = gSum(V*alpha1.primitiveField());
        const scalar minUnclipped = gMin(alpha1.primitiveField());
        const scalar maxUnclipped = gMax(alpha1.primitiveField());

        if (step == 1)
        {
            const fileName dir(outDir/"step1");
            const surfaceScalarField& dVfLimited =
                mesh.lookupObject<surfaceScalarField>("dVf_");
            {
                OFstream os(dir/"faces.dat");
                os.precision(17);
                os << "# phi dVfUnlimited dVfLimited" << nl;
                for (label facei = 0; facei < mesh.nFaces(); ++facei)
                {
                    os  << faceValue(phi, facei)
                        << token::SPACE << faceValue(dVfUnlimited(), facei)
                        << token::SPACE << faceValue(dVfLimited, facei) << nl;
                }
            }
            {
                // copies after 0, 1, 2 iterations (alpha1 after 3 if they
                // all exceed the bounds), unclipped alpha1
                OFstream os(dir/"cells.dat");
                os.precision(17);
                os  << "# Ux Uy Uz alpha0 alphaBounds0 alphaBounds1"
                    << " alphaBounds2 alphaUnclipped V" << nl;
                forAll(U, celli)
                {
                    writeVector(os, U[celli]);
                    os << token::SPACE << alpha1.oldTime()[celli];
                    for (label n = 0; n < 3; ++n)
                    {
                        const scalarField& a =
                            boundsStep1[n].size()
                          ? boundsStep1[n]
                          : alpha1.primitiveField();
                        os << token::SPACE << a[celli];
                    }
                    os  << token::SPACE << alpha1[celli]
                        << token::SPACE << V[celli] << nl;
                }
            }
            {
                const reconstructionSchemes& surf = advector->surf();
                interpolationCellPoint<vector> UInterp(U);
                OFstream os(dir/"interface.dat");
                os.precision(17);
                os << "# cell nx ny nz x0x x0y x0z n0x n0y n0z Un0" << nl;
                for (const label celli : surf.interfaceLabels())
                {
                    if (mag(surf.normal()[celli]) == 0)
                    {
                        continue;
                    }
                    const point x0(surf.centre()[celli]);
                    const vector n0(normalised(-surf.normal()[celli]));
                    os << celli;
                    writeVector(os, surf.normal()[celli]);
                    writeVector(os, x0);
                    writeVector(os, n0);
                    os << token::SPACE
                       << (UInterp.interpolate(x0, celli) & n0) << nl;
                }
            }
        }

        // applyBruteForceBounding with clip true, snapTol 0
        alpha1.clamp_range(zero_one{});
        alpha1.correctBoundaryConditions();

        if (step == 1)
        {
            checkEqual
            (
                tclipped().primitiveField(), alpha1.primitiveField(),
                "alpha clipped by isoAdvection and by the utility"
            );
        }

        label nSurfaceCells = 0;
        for (const label celli : advector->surf().interfaceLabels())
        {
            nSurfaceCells += mag(advector->surf().normal()[celli]) != 0;
        }

        stepsOs
            << step << token::SPACE << runTime.value()
            << token::SPACE << runTime.deltaTValue()
            << token::SPACE << CoNum << token::SPACE << alphaCoNum
            << token::SPACE << nIter << token::SPACE << nSurfaceCells
            << token::SPACE << massUnclipped
            << token::SPACE << minUnclipped << token::SPACE << maxUnclipped
            << token::SPACE << gSum(V*alpha1.primitiveField())
            << token::SPACE << gMin(alpha1.primitiveField())
            << token::SPACE << gMax(alpha1.primitiveField()) << nl;

        if
        (
            step == 1
         || (alphaInterval > 0 && step % alphaInterval == 0)
         || runTime.writeTime()
        )
        {
            writeAlpha
            (
                outDir/"alpha"/(Foam::name(step) + ".dat"),
                alpha1.primitiveField()
            );
        }

        Info<< "Step " << step << " t = " << runTime.value()
            << " dt = " << runTime.deltaTValue()
            << " nIter = " << nIter << endl;
    }

    Info<< "End\n" << endl;

    return 0;
}


// ************************************************************************* //
