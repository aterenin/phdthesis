using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true)
using Colors
using Distributions
using Random
using KernelFunctions

preamble = [raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex(file, axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{figures/$(replace(file, ".tex" => ".pdf"))}", p, use_default_preamble=false, preamble = preamble))

x = 0:0.02:1
x12 = 0:0.005:1
n = 8
a = 0.075
ls = 0.1

k12 = a * with_lengthscale(Matern12Kernel(), ls)
k32 = a * with_lengthscale(Matern32Kernel(), ls)
k52 = a * with_lengthscale(Matern52Kernel(), ls)

K12 = kernelmatrix(k12, x12, x12)
K32 = kernelmatrix(k32, x, x)
K52 = kernelmatrix(k52, x, x)

Random.seed!(15)
samples_12 = rand(MvNormal(zeros(length(x12)), K12), n)
samples_32 = rand(MvNormal(zeros(length(x)), K32), n)
samples_52 = rand(MvNormal(zeros(length(x)), K52), n)

l = 4096
r = rand(Normal(0,1/(2*pi*ls)),l)
w = rand(Normal(0,1),2*l,n)
phi(x) = vcat(sin.(2*pi*r.*x'),cos.(2*pi*r.*x'))
f(x) = sqrt(a/l) * phi(x)' * w
samples_inf = f(x)

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
            thick,
            color=colorant"#1f77b4",
        },
        Coordinates(x12, samples_12[:,i])
    ) for i in 1:n]...,
) |> save_tex("tex/gp-sm-12.tex")

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
        },
        Coordinates(x, samples_32[:,i])
    ) for i in 1:n]...,
) |> save_tex("tex/gp-sm-32.tex")


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
        },
        Coordinates(x, samples_52[:,i])
    ) for i in 1:n]...,
) |> save_tex("tex/gp-sm-52.tex")

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
        },
        Coordinates(x, samples_inf[:,i])
    ) for i in 1:n]...,
) |> save_tex("tex/gp-sm-inf.tex")


