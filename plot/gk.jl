include("plot.jl")
using Colors
using ColorSchemes
using DelimitedFiles
using Statistics

for graph_name in ("comp","star","reg","ba")
    graph = readdlm("../results/ggp/gk_$(graph_name).csv", ',')
    edges = readdlm("../results/ggp/gk_$(graph_name)_edge.csv", ',', Int) .+ 1
    y_max = if graph_name == "comp" || graph_name == "star" 1.25 else 1.5 end
    height = if graph_name == "comp" || graph_name == "star" "4.5cm" else "5cm" end
    @pgf Axis(
            {
                axis_lines = "none",
                height = height,
                width = "6cm",
                xmin=-1.25, xmax=1.25, ymin=-1.25, ymax=y_max,
            },
            [raw"\node at (-1.25,-1.25) {};"],
            [raw"\node at (-1.25,1.25) {};"],
            [raw"\node at (1.25,1.25) {};"],
            [raw"\node at (1.25,-1.25) {};"],
            ["\\node at (0,$(y_max)) {};"],
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


@pgf Axis(
    {
        hide_axis,
        xmin = 0,
        xmax = 1,
        ymin = 0,
        ymax = 1,
        legend_columns = -1, 
        legend_style = raw"draw={none}, legend cell align={center}, font={\footnotesize}, column sep={0.0625cm}, /tikz/every even column/.append style={column sep=0.375cm}",
        colormap = colorscheme_to_pgf("viridis"),
    },
    legend_entry("empty legend" => raw"\quad"),
    legend_entry("only marks, mark size={2.5pt}, color=$(color_to_pgf(ColorSchemes.viridis[192]))" => "Nodes"),
    legend_entry("very thick, color=$(color_to_pgf(weighted_color_mean(0.25, colorant"#000000", colorant"#ffffff")))" => "Edges"),
    legend_entry("draw opacity={0}, area legend, shading={viridisshading}, shade" => raw"Prior variance"),
    [raw"\pgfplotscolormaptoshadingspec{viridis}{2cm}\viridisshadingspec"],
    [raw"\def\tempdeclare{\pgfdeclarehorizontalshading{viridisshading}{3cm}}"],
    [raw"\expandafter\tempdeclare\expandafter{\viridisshadingspec}"],
) |> a -> TikzPicture(PGFPlotsX.Options(:rotate => 90, :transform_shape => nothing), a) |> save_tex("gk-lgnd.tex")