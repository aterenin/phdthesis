using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true)
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

preamble = [raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex(file, axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{$(replace(file, ".tex" => ""))}", p, use_default_preamble=false, preamble = preamble))

z = range(0.4,0.7;length=10)
u = 0.5*sin.(10 .* (z .- 0.55))

x = -0.25:0.0125:1.25
a = 0.1
ls = 0.1
s = 0.000001^2
l = 128
n = 32

Random.seed!(1)
r = rand(Normal(0,1/(2*pi*ls)),l)
b = rand(Uniform(0,2*pi),l)
w = rand(Normal(0,1),2*l,n)
e = rand(MvNormal(zeros(length(z)), s*I),n)

phi(x) = sqrt(a/l) * vcat(sin.(2*pi*r.*x'),cos.(2*pi*r.*x'))
f(x) = phi(x)' * w

f_cond = f(x) + phi(x)' * phi(z) * ((phi(z)' * phi(z) + s*I) \ (u .- f(z) .- e))

m_cond = phi(x)' * phi(z) * ((phi(z)' * phi(z) + s*I) \ u)
K_cond = Symmetric(phi(x)' * phi(x) - phi(x)' * phi(z) * ((phi(z)' * phi(z) + s*I) \ (phi(z)' * phi(x))))

k = a * with_lengthscale(SqExponentialKernel(), ls)
K_xx = kernelmatrix(k, x, x)
K_xz = kernelmatrix(k, x, z)
K_zz = kernelmatrix(k, z, z)

m_true = K_xz * ((K_zz + s*I) \ u)
K_true = Symmetric(K_xx - K_xz * ((K_zz + s*I) \ K_xz'))




@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "9.75cm",
        xmin=-0.15, xmax=1.25, ymin=-1, ymax=1,
    },
    [raw"\node at (-0.15,-1) {};"],
    [raw"\node at (-0.15,1) {};"],
    [raw"\node at (1.25,1) {};"],
    [raw"\node at (1.25,-1) {};"],
    Plot(
        {
            no_markers,
            smooth,
            very_thick,
            color=colorant"#1f77b4",
            name_path = "upper",
        },
        Coordinates(x, m_cond + 1.96*sqrt.(diag(K_cond)))
    ),
    Plot(
        {
            no_markers,
            smooth,
            very_thick,
            color=colorant"#1f77b4",
            name_path = "lower",
        },
        Coordinates(x, m_cond - 1.96*sqrt.(diag(K_cond)))
    ),
    Plot(
        {
            color=colorant"#1f77b4",
            opacity = 0.25
        },
        raw"fill between [of = upper and lower]",
    ),
    Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colorant"#1f77b4",
        },
        Coordinates(x, m_cond)
    ),
    Plot(
        {
            no_markers,
            smooth,
            thick,
            dashed,
        },
        Coordinates(x, m_true + 1.96*sqrt.(diag(K_true)))
    ),
    Plot(
        {
            no_markers,
            smooth,
            thick,
            dashed,
        },
        Coordinates(x, m_true - 1.96*sqrt.(diag(K_true)))
    ),
    Plot(
        {
            no_markers,
            smooth,
            very_thick,
            dashed,
            
        },
        Coordinates(x, m_true)
    ),
    [Plot(
        {
            no_markers,
            smooth,
            thick,
            color=colorant"#1f77b4",
            opacity = 0.5
        },
        Coordinates(x, f_cond[:,i])
    ) for i in 1:n]...,
    Plot(
        { 
            only_marks,
            mark="|",
            mark_size="4pt",
            thick,
            color=colorant"#1f77b4",
        },
        Coordinates(z, u)
    ),
) |> save_tex("tex/gp-vs.tex")
