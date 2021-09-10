include("plot.jl")
using Colors
using KernelFunctions

k = 2.5 * Matern12Kernel()
periodic_sum = sum(k.(0, reshape(range(-pi * 1025, pi * 1025, length=129 * 1025), (129,:))), dims=2) |> vec


@pgf Axis(
    {
        axis_lines = "none",
        height = "6.5cm",
        axis_equal,
        view = "{300}{25}"
    },
    Plot3(
        {
            no_markers,
            domain = "0:2*pi",
            smooth_cycle,
            samples = 128,
            samples_y = 0,
            dashed,
            very_thick,
            color = colorant"#7f7f7f",
        },
        "({cos(deg(x))},{sin(deg(x))},{0})"
    ),
    Plot3(
        {
            no_markers,
            dashed,
            very_thick,
            color = colorant"#7f7f7f"
        },
        Coordinates([1,1],[0,0],[0,maximum(periodic_sum)])
    ),
    Plot3(
        {
            only_marks,
            mark_size="2pt",
            color = "black"
        },
        Coordinates([cos(0)],[sin(0)],[0])
    ),
    Plot3(
        {
            no_markers,
            ultra_thick,
            color = colorant"#1f77b4",
        },
        Coordinates(cos.(range(-pi,pi,length=length(periodic_sum))), sin.(range(-pi,pi,length=length(periodic_sum))), periodic_sum)
    ),
) |> TikzPicture |> save_tex("s1-ker.tex")


for eigen_idx in (4,16)
    @pgf Axis(
            {
                axis_lines = "none",
                height = "4cm",
                width = "4cm",
                xmin=-1.5, xmax=1.5, ymin=-1.5, ymax=1.5,
            },
            [raw"\node at (-1.5,-1.5) {};"],
            [raw"\node at (-1.5,1.5) {};"],
            [raw"\node at (1.5,1.5) {};"],
            [raw"\node at (1.5,-1.5) {};"],
            Plot(
                {
                    domain = "0:2*pi",
                    smooth_cycle,
                    samples = 128,
                    dashed,
                    color = colorant"#7f7f7f",
                    very_thick,
                },
                "({cos(deg(x))},{sin(deg(x))})"
            ),
            Plot(
                {
                    domain = "0:2*pi",
                    smooth_cycle,
                    samples = 128,
                    ultra_thick,
                    color = colorant"#1f77b4",
                },
                "({(1 + 0.25 * cos(deg($(eigen_idx)*x))) * cos(deg(x))},{(1 + 0.25 * cos(deg($(eigen_idx)*x))) * sin(deg(x))})"
            )
        ) |> TikzPicture |> save_tex("s1-e$(eigen_idx).tex")
end