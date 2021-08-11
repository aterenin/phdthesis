using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true); push!(PGFPlotsX.CLASS_OPTIONS, "11pt")
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex("../figures/tex/$file", axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{figures/tex/$(replace(file, ".tex" => ".pdf"))}", p, use_default_preamble=false, preamble = preamble))

z = [0.5,0.75]
u = [0.15,-0.15]
x = 0:0.0125:1
a = 0.1
ls = 0.1
k = a * with_lengthscale(Matern52Kernel(), ls)
s = 0.01
l = 32

K_xx = kernelmatrix(k, x, x)
K_xz = kernelmatrix(k, x, z)
K_zz = kernelmatrix(k, z, z)

m_cond = K_xz * ((K_zz + s*I) \ u)
K_cond = Symmetric(K_xx - K_xz * ((K_zz + s*I) \ K_xz'))

dist_cond = MvNormal(m_cond, K_cond)
Random.seed!(1)
samples_cond = rand(dist_cond, l)

@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=0, xmax=1, ymin=-1, ymax=1,
    },
    [raw"\node at (0,-1) {};"],
    [raw"\node at (0,1) {};"],
    [raw"\node at (1,1) {};"],
    [raw"\node at (1,-1) {};"],
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
            only_marks,
            mark_size="3pt",
            fill=colorant"#1f77b4",
        },
        Coordinates(z, u)
    ),
) |> save_tex("gp-dist-cond.tex")


@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=0, xmax=1, ymin=-1, ymax=1,
    },
    [raw"\node at (0,-1) {};"],
    [raw"\node at (0,1) {};"],
    [raw"\node at (1,1) {};"],
    [raw"\node at (1,-1) {};"],
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
    [Plot(
        {
            no_markers,
            smooth,
            thick,
            color=colorant"#1f77b4",
            opacity = 0.5
        },
        Coordinates(x, samples_cond[:,i])
    ) for i in 1:l]...,
    Plot(
        { 
            only_marks,
            mark_size="3pt",
            fill=colorant"#1f77b4",
        },
        Coordinates(z, u)
    ),
) |> save_tex("gp-dist-samples.tex")
