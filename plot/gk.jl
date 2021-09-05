include("plot.jl")
using Colors
using ColorSchemes
using DelimitedFiles
using Statistics

for graph_name in ("comp","star","reg","ba")
    graph = readdlm("../results/ggp/gk_$(graph_name).csv", ',')
    edges = readdlm("../results/ggp/gk_$(graph_name)_edge.csv", ',', Int) .+ 1
    @pgf Axis(
            {
                axis_lines = "none",
                height = "5cm",
                width = "6.5cm",
                xmin=-1.0625, xmax=1.0625, ymin=-1.0625, ymax=1.0625,
            },
            [raw"\node at (-1.0625,-1.0625) {};"],
            [raw"\node at (-1.0625,1.0625) {};"],
            [raw"\node at (1.0625,1.0625) {};"],
            [raw"\node at (1.0625,-1.0625) {};"],
            [Plot(
                {
                    no_markers,
                    very_thick,
                    color = weighted_color_mean(0.25, colorant"#000000", colorant"#ffffff"),
                },
                Coordinates([graph[e1,1],graph[e2,1]],[graph[e1,2],graph[e2,2]])
            ) for (e1,e2) in eachrow(edges)]...,
            Plot(
                { 
                    only_marks,
                    scatter,
                    scatter_src="explicit",
                    colormap = colorscheme_to_pgf("viridis"),
                    mark_size="5pt",
                    draw_opacity = 0,
                },
                Table(
                    {
                        meta = "color",
                    },
                    x = vcat(-2,graph[:,1],2),
                    y = vcat(0,graph[:,2],0),
                    color = vcat(0,graph[:,3],1.25),
                ),
            ),
        ) |> TikzPicture |> save_tex("gk-$graph_name.tex")
end

