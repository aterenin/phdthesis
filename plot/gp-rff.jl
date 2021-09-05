include("plot.jl")
using Colors
using Distributions
using Random

x = -0.5:0.0125:0.5
a = 0.1
ls = 0.1
l = 4096
L = 2
n = 32

Random.seed!(7)
r = rand(Normal(0,1/(2*pi*ls)),l)
w = rand(Normal(0,1),2*l,n)

phi(x) = vcat(sin.(2*pi*r.*x'),cos.(2*pi*r.*x'))
f(x) = sqrt(a/l) * phi(x)' * w

basis_rff = phi(x)'
samples_rff = f(x)

colors = range(weighted_color_mean(2/3, colorant"#1f77b4",colorant"white"), weighted_color_mean(2/3, colorant"#1f77b4",colorant"black"); length=2*L)


@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=-0.5, xmax=0.5, ymin=-2.5, ymax=2.5,
    },
    [raw"\node at (-0.5,-2.5) {};"],
    [raw"\node at (-0.5,2.5) {};"],
    [raw"\node at (0.5,2.5) {};"],
    [raw"\node at (0.5,-2.5) {};"],
    [Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colors[i],
        },
        Coordinates(x, basis_rff[:,vcat(1:L,l+1:l+L)[i]])
    ) for i in 1:2*L]...,
) |> TikzPicture |> save_tex("gp-rff-basis.tex")



@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
    },
    [raw"\node at (-0.5,-1) {};"],
    [raw"\node at (-0.5,1) {};"],
    [raw"\node at (0.5,1) {};"],
    [raw"\node at (0.5,-1) {};"],
    [Plot(
        {
            no_markers,
            smooth,
            thick,
            color=colorant"#1f77b4",
            opacity = 0.5
        },
        Coordinates(x, samples_rff[:,i])
    ) for i in 1:n]...,
) |> TikzPicture |> save_tex("gp-rff-samples.tex")
