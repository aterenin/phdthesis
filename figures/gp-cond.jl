using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true); push!(PGFPlotsX.CLASS_OPTIONS, "11pt")
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex(file, axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{figures/$(replace(file, ".tex" => ".pdf"))}", p, use_default_preamble=false, preamble = preamble))

z = range(-0.225,0.25;length=4)
u = -z

x = -0.5:0.0125:0.5
a = 0.1
ls = 0.1
s = 0.00001
l = 128
n = 32
L = 2
M = 4

k = a * with_lengthscale(SqExponentialKernel(), ls)
K_xx = kernelmatrix(k, x, x)
K_xz = kernelmatrix(k, x, z)
K_zz = kernelmatrix(k, z, z)

Random.seed!(2)
r = rand(Normal(0,1/(2*pi*ls)),l)
b = rand(Uniform(0,2*pi),l)
w = rand(Normal(0,1),2*l,n)
e = rand(MvNormal(zeros(length(z)), s*I),n)

phi(x) = sqrt(a/l) * vcat(sin.(2*pi*r.*x'),cos.(2*pi*r.*x'))
f(x) = phi(x)' * w

f_prior = f(x)
f_update = K_xz * ((K_zz + s*I) \ (u .- f(z) .- e))
f_cond = f_prior + f_update

m_cond = K_xz * ((K_zz + s*I) \ u)
K_cond = Symmetric(K_xx - K_xz * ((K_zz + s*I) \ K_xz'))

basis_rff = sqrt(l/a) * phi(x)'
colors_rff = range(weighted_color_mean(2/3, colorant"#1f77b4",colorant"white"), weighted_color_mean(2/3, colorant"#1f77b4",colorant"black"); length=2*L)
colors_ip = range(weighted_color_mean(2/3, colorant"#1f77b4",colorant"white"), weighted_color_mean(2/3, colorant"#1f77b4",colorant"black"); length=M)



@pgf GroupPlot(
    {
        group_style = { 
            group_size = "5 by 2",
            horizontal_sep = "0pt",
            vertical_sep = "0pt",
        },
    },
    Axis(
        {
            axis_lines = "none",
            height = "4.5cm",
            width = "6cm",
            xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
            title = "Prior",
            title_style = { yshift = "-0.125cm" },
        },
        [raw"\node at (-0.5,-1) {};"],
        [raw"\node at (-0.5,1) {};"],
        [raw"\node at (0.5,1) {};"],
        [raw"\node at (0.5,-1) {};"],
        [Plot(
            {
                no_markers,
                dashed,
                black,
                thick,
            },
            Coordinates([(z[i], u[i]), (z[i], f(z[i])[1])])
        ) for i in 1:4],
        Plot(
            {
                no_markers,
                smooth,
                ultra_thick,
                color=colorant"#1f77b4",
            },
            Coordinates(x, f_prior[:,1])
        ),
        Plot(
            { 
                only_marks,
                fill=colorant"#1f77b4",
            },
            Coordinates(z, u)
        ),
    ),
    Axis(
        {
            axis_lines = "none",
            height = "4.5cm",
            width = "3cm",
            xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
        },
        [raw"\node at (-0.5,-1) {};"],
        [raw"\node at (-0.5,1) {};"],
        [raw"\node at (0.5,1) {};"],
        [raw"\node at (0.5,-1) {};"],
        [raw"\node[scale=2] at (0,0) {+};"],
    ),
    Axis(
        {
            axis_lines = "none",
            height = "4.5cm",
            width = "6cm",
            xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
            title = "Update",
            title_style = { yshift = "-0.125cm" },
        },
        [raw"\node at (-0.5,-1) {};"],
        [raw"\node at (-0.5,1) {};"],
        [raw"\node at (0.5,1) {};"],
        [raw"\node at (0.5,-1) {};"],
        Plot(
            {
                no_markers,
                smooth,
                ultra_thick,
                color=colorant"#1f77b4",
            },
            Coordinates(x, f_update[:,1])
        ),
        HLine(
            { 
                dashed,
                black,
                thick,
            }, 
            0
        ),
    ),
    Axis(
        {
            axis_lines = "none",
            height = "4.5cm",
            width = "3cm",
            xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
        },
        [raw"\node at (-0.5,-1) {};"],
        [raw"\node at (-0.5,1) {};"],
        [raw"\node at (0.5,1) {};"],
        [raw"\node at (0.5,-1) {};"],
        [raw"\node[scale=2] at (0,0) {=};"],
    ),
    Axis(
        {
            axis_lines = "none",
            height = "4.5cm",
            width = "6cm",
            xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
            title = "Posterior",
            title_style = { yshift = "-0.125cm" },
        },
        [raw"\node at (-0.5,-1) {};"],
        [raw"\node at (-0.5,1) {};"],
        [raw"\node at (0.5,1) {};"],
        [raw"\node at (0.5,-1) {};"],
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
            Coordinates(x, f_cond[:,1])
        ),
        Plot(
            { 
                only_marks,
                fill=colorant"#1f77b4",
            },
            Coordinates(z, u)
        ),
    ),
    Axis(
        {
            axis_lines = "none",
            height = "2.5cm",
            width = "6cm",
            xmin=-0.5, xmax=0.5, ymin=-1.25, ymax=1.25,
        },
        [raw"\node at (-0.5,-1.25) {};"],
        [raw"\node at (-0.5,1.25) {};"],
        [raw"\node at (0.5,1.25) {};"],
        [raw"\node at (0.5,-1.25) {};"],
        [Plot(
            {
                no_markers,
                smooth,
                ultra_thick,
                color=colors_rff[i],
            },
            Coordinates(x, basis_rff[:,vcat(1:L,l+1:l+L)[i]])
        ) for i in 1:2*L]...,
    ),
    Axis(
        {
            axis_lines = "none",
            height = "3cm",
            width = "3cm",
            xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
        },
        [raw"\node at (-0.5,-1) {};"],
        [raw"\node at (-0.5,1) {};"],
        [raw"\node at (0.5,1) {};"],
        [raw"\node at (0.5,-1) {};"],
    ),
    Axis(
        {
            axis_lines = "none",
            height = "2.5cm",
            width = "6cm",
            xmin=-0.5, xmax=0.5, ymin=-0.025, ymax=0.125,
        },
        [raw"\node at (0,-0.025) {};"],
        [raw"\node at (0,0.125) {};"],
        [raw"\node at (1,0.125) {};"],
        [raw"\node at (1,-0.025) {};"],
        [Plot(
            {
                no_markers,
                smooth,
                ultra_thick,
                color=colors_ip[i],
            },
            Coordinates(x, K_xz[:,(1:M)[i]])
        ) for i in 1:M]...,
    )
 ) |> save_tex("tex/gp-cond.tex")
