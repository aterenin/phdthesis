include("plot.jl")
using Colors
using Distributions
using Random

dist_1 = Normal(0, 1)
dist_2 = Normal(-5, 2)
dist_3 = Normal(3, 0.5)
dist_4 = Normal(6.5, 1.25)

x = -12:0.125:12

pdf_1 = [pdf(dist_1, a) for a in x]
pdf_2 = [pdf(dist_2, a) for a in x]
pdf_3 = [pdf(dist_3, a) for a in x]
pdf_4 = [pdf(dist_4, a) for a in x]

density = [pdf_1,pdf_2,pdf_3,pdf_4]

@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "12cm",
        xmin=-10, xmax=10, ymin=-0.25, ymax=1,
        
    },
    [raw"\node at (0,-0.25) {};"],
    [raw"\node at (0,1) {};"],
    [Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colorant"#1f77b4",
            fill=colorant"#1f77b4",
            fill_opacity = 0.25,
        },
        Coordinates(x, density[i])
    ) for i in 1:length(density)]...,
    HLine(
        { 
            black,
            ultra_thick,
        }, 
        0
    ),
) |> TikzPicture |> save_tex("norm-dist.tex")
