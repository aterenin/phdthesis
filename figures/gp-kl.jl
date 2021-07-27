using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true)
using Colors
using Distributions
using Random
using LinearAlgebra: Diagonal

preamble = [raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex(file, axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{figures/$(replace(file, ".tex" => ".pdf"))}", p, use_default_preamble=false, preamble = preamble))



x = 0:0.0125:1
a = 0.05
ls = 0.2
l = 256
L = 4
n = 32

Random.seed!(2)
w = rand(Normal(0,1),l,n)

eigvals = [(pi*m)^2 for m in 1:l]
rho = exp.(.-ls.^2 .* eigvals ./ 2) |> Diagonal
phi(x) = sin.(pi * (1:l) .* x')
f(x) = sqrt(2*a) * phi(x)' * sqrt.(rho) * w

basis_kl = phi(x)'
samples_kl = f(x)

colors = range(weighted_color_mean(2/3, colorant"#1f77b4",colorant"white"), weighted_color_mean(2/3, colorant"#1f77b4",colorant"black"); length=L)



@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=0, xmax=1, ymin=-2.5, ymax=2.5,
    },
    [raw"\node at (0,-2.5) {};"],
    [raw"\node at (0,2.5) {};"],
    [raw"\node at (1,2.5) {};"],
    [raw"\node at (1,-2.5) {};"],
    [Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colors[i],
        },
        Coordinates(x, basis_kl[:,(1:L)[i]])
    ) for i in 1:L]...,
) |> save_tex("tex/gp-kl-basis.tex")



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
        Coordinates(x, samples_kl[:,i])
    ) for i in 1:n]...,
) |> save_tex("tex/gp-kl-samples.tex")
