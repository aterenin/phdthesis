using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true)
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

preamble = [raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex(file, axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{$(replace(file, ".tex" => ""))}", p, use_default_preamble=false, preamble = preamble))

z = 0.4:0.05:0.7
u = zeros(length(z))
d = 0.4:0.01:0.7
y = zeros(length(d))
x = 0:0.0125:1
a = 0.1
ls = 0.15
k = a * with_lengthscale(Matern52Kernel(), ls)
s = 0.000001
l = 32
L = length(z)

idx_z = [findfirst(v -> v==w, x) for w in z]

K_xx = kernelmatrix(k, x, x)
K_xz = kernelmatrix(k, x, z)
K_zz = kernelmatrix(k, z, z)
K_dz = kernelmatrix(k, d, z)

m_cond = K_xz * ((K_zz + s*I) \ u)
K_cond = Symmetric(K_xx - K_xz * ((K_zz + s*I) \ K_xz'))

Random.seed!(4)
dist_joint = MvNormal(zeros(length(x)), K_xx)
samples_joint = rand(dist_joint, l) 

dist_inducing = MvNormal(zeros(length(z)), Symmetric(K_zz * (K_zz + K_dz' * K_dz / s^2) \ K_zz) )
samples_inducing = rand(dist_inducing, l)

samples_cond = samples_joint + K_xz * (K_zz \ (samples_inducing .- samples_joint[idx_z,:]))
samples_canonical = K_xz * (K_zz \ (samples_inducing .- samples_joint[idx_z,:]))
 
colors = range(weighted_color_mean(2/3, colorant"#1f77b4",colorant"white"), weighted_color_mean(2/3, colorant"#1f77b4",colorant"black"); length=L)


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
            mark="|",
            mark_size="4pt",
            thick,
            color=colorant"#1f77b4",
        },
        Coordinates(d, y)
    ),
    Plot(
        { 
            only_marks,
            fill=colorant"#1f77b4",
        },
        Coordinates(z, u)
    ),
) |> save_tex("tex/gp-ip-cond.tex")


@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=0, xmax=1, ymin=-0.1, ymax=0.2,
    },
    [raw"\node at (0,-0.1) {};"],
    [raw"\node at (0,0.2) {};"],
    [raw"\node at (1,0.2) {};"],
    [raw"\node at (1,-0.1) {};"],
    [Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colors[i],
        },
        Coordinates(x, K_xz[:,(1:L)[i]])
    ) for i in 1:L]...,
) |> save_tex("tex/gp-ip-basis.tex")



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
    [Plot(
        {
            no_markers,
            smooth,
            thick,
            color=colorant"#1f77b4",
            opacity = 0.5
        },
        Coordinates(x, samples_canonical[:,i])
    ) for i in 1:l]...,
) |> save_tex("tex/gp-ip-samples.tex")
