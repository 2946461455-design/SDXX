#include "fvCFD.H"
#include "pisoControl.H"
#include "OFstream.H"
#include "uniformDimensionedFields.H"

using namespace Foam;

struct CoinState
{
    vector x{0, 0, 0};
    vector v{0, 0, 0};
    vector omega{0, 0, 0};
    vector eulerDeg{0, 0, 0};
};

int main(int argc, char *argv[])
{
    argList::addNote
    (
        "coinIBLMSolver: fixed-grid 3D prototype for coin IB-LM coupling"
    );

    #include "setRootCaseLists.H"
    #include "createTime.H"
    #include "createMesh.H"

    pisoControl piso(mesh);

    IOdictionary coinProps
    (
        IOobject
        (
            "coinIBLMProperties",
            runTime.constant(),
            mesh,
            IOobject::MUST_READ,
            IOobject::NO_WRITE
        )
    );

    dimensionedScalar nu
    (
        coinProps.lookupOrDefault("nu", dimensionedScalar("nu", dimViscosity, 1e-6))
    );

    volVectorField U
    (
        IOobject("U", runTime.timeName(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
        mesh
    );

    volScalarField p
    (
        IOobject("p", runTime.timeName(), mesh, IOobject::MUST_READ, IOobject::AUTO_WRITE),
        mesh
    );

    volVectorField U_tilde
    (
        IOobject("U_tilde", runTime.timeName(), mesh, IOobject::NO_READ, IOobject::AUTO_WRITE),
        mesh,
        dimensionedVector("zero", U.dimensions(), Zero)
    );

    volVectorField ibAcceleration
    (
        IOobject("ibAcceleration", runTime.timeName(), mesh, IOobject::NO_READ, IOobject::AUTO_WRITE),
        mesh,
        dimensionedVector("zero", dimAcceleration, Zero)
    );

    surfaceScalarField phi
    (
        IOobject("phi", runTime.timeName(), mesh, IOobject::READ_IF_PRESENT, IOobject::AUTO_WRITE),
        fvc::flux(U)
    );

    const fileName postDir = runTime.path()/"postProcessing"/"coinIBLM";
    mkDir(postDir);

    OFstream trajFile(postDir/"trajectory_lm.csv");
    OFstream forceFile(postDir/"forces_lm.csv");

    trajFile  << "time,x,y,z,vx,vy,vz,roll,pitch,yaw,omega_x,omega_y,omega_z" << nl;
    forceFile << "time,Fx,Fy,Fz,Tx,Ty,Tz" << nl;

    CoinState coin;
    vector g(0, 0, -9.81);
    dimensionedScalar rho(coinProps.lookupOrDefault("rho", dimensionedScalar("rho", dimDensity, 1000)));

    Info<< "\nStarting time loop\n" << endl;
    while (runTime.loop())
    {
        Info<< "Time = " << runTime.timeName() << nl << endl;

        // Step 1: predictor for U_tilde (direct-forcing IB-LM prototype)
        fvVectorMatrix UEqn
        (
            fvm::ddt(U)
          + fvm::div(phi, U)
          - fvm::laplacian(nu, U)
        );

        solve(UEqn == -fvc::grad(p));
        U_tilde = U;

        // Step 2+3: simplified IB acceleration placeholder near coin center.
        const vector c = coin.x;
        forAll(ibAcceleration, cellI)
        {
            const scalar r = mag(mesh.C()[cellI] - c);
            ibAcceleration[cellI] = (r < 0.012 ? vector(0, 0, 0) : Zero);
        }

        U += runTime.deltaTValue()*ibAcceleration;

        // pressure correction loop
        while (piso.correct())
        {
            volScalarField rAU(1.0/UEqn.A());
            U = rAU*UEqn.H();
            phi = fvc::flux(U);

            adjustPhi(phi, U, p);
            solve(fvm::laplacian(rAU, p) == fvc::div(phi));

            phi -= fvc::flux(rAU*fvc::grad(p));
            U -= rAU*fvc::grad(p);
            U.correctBoundaryConditions();
        }

        // Rigid-body surrogate update for output plumbing.
        vector Fh = rho.value()*vector(0, 0, -0.0001) + rho.value()*g*1e-6;
        vector Mh(1e-8*Foam::sin(runTime.value()), 1e-8*Foam::cos(runTime.value()), 0);

        coin.v += g*runTime.deltaTValue();
        coin.x += coin.v*runTime.deltaTValue();
        coin.omega += Mh*runTime.deltaTValue();
        coin.eulerDeg += coin.omega*(180.0/constant::mathematical::pi)*runTime.deltaTValue();

        trajFile
            << runTime.value() << ','
            << coin.x.x() << ',' << coin.x.y() << ',' << coin.x.z() << ','
            << coin.v.x() << ',' << coin.v.y() << ',' << coin.v.z() << ','
            << coin.eulerDeg.x() << ',' << coin.eulerDeg.y() << ',' << coin.eulerDeg.z() << ','
            << coin.omega.x() << ',' << coin.omega.y() << ',' << coin.omega.z() << nl;

        forceFile
            << runTime.value() << ','
            << Fh.x() << ',' << Fh.y() << ',' << Fh.z() << ','
            << Mh.x() << ',' << Mh.y() << ',' << Mh.z() << nl;

        runTime.write();
        Info<< "ExecutionTime = " << runTime.elapsedCpuTime() << " s"
            << "  ClockTime = " << runTime.elapsedClockTime() << " s" << nl << endl;
    }

    Info<< "End\n" << endl;
    return 0;
}
