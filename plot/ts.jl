include("plot.jl")
using Colors
using DelimitedFiles
using Statistics

data = Dict((d,l,c) => readdlm("../results/ts/ts_regret_d$(d)_l$(l)_$(c).csv", ',') for d in (2,4,8) for l in (256,1024,4096) for c in ("direct","cholesky","rff","random","pathwise"))
color = Dict("direct" => "black", "cholesky" => colorant"#2ca02c", "rff" => colorant"#ff7f0e", "random" => "black","pathwise" => colorant"#1f77b4")

@pgf GroupPlot(
    {
        group_style = { 
            group_size = "3 by 3",
            horizontal_sep = "1cm",
            vertical_sep = "1.5cm",
        },
    },
    [Axis(
        merge(
            {
                height = "5.625cm",
                width = "5.625cm",
                separate_axis_lines, 
                "axis x line*={bottom}",
                "axis y line*={left}",
                axis_x_line_shift = "10pt",
                axis_y_line_shift = "10pt",
                xlabel_shift = "10pt",
                ylabel_shift = "10pt",
                minor_tick_num = 1,
                grid = "both",
                xtick_align="outside",
                ytick_align="outside",
                enlarge_x_limits = false,
                enlarge_y_limits = false,
                x_axis_line_style = { cap = "rect" },
                y_axis_line_style = { cap = "rect" },
                "every tick/.style={black, thin}",
                grid_style = { black, opacity = 0.1, cap = "rect" },
                title_style = { anchor = "base", yshift = "0.125cm", font = raw"\small" },
                label_style = { font = raw"\small" },
                tick_label_style = { font = raw"\small" },
                x_tick_label_style = "/pgf/number format/1000 sep=",
                legend_columns = -1, 
                legend_style = raw"draw={none}, fill={none}, at={(0.425,1.2)}, anchor={south}, font={\footnotesize}, column sep={0.0625cm}, /tikz/every even column/.append style={column sep={0.375cm}}"
            },
            l == 256 ? PGFPlotsX.Options() : PGFPlotsX.Options(:ytick_style => "draw={none}", :yticklabels => ",,", :y_axis_line_style => "draw={none}"),
            PGFPlotsX.Options(:xtick => d == 2 ? "1,16,32,48,64" : d == 4 ? "1,64,128,192,256" : "1,256,512,768,1024"),
            PGFPlotsX.Options(:ymin => d == 8 ? -2 : -3),
            PGFPlotsX.Options(:ymax => 1),
            d == 2 ? PGFPlotsX.Options(:title => "\$\\ell = $l\$") : PGFPlotsX.Options(),
            l == 4096 ? PGFPlotsX.Options(:ylabel => "\$d = $d\$") : PGFPlotsX.Options(),
            l == 4096 ? PGFPlotsX.Options(:ylabel_style => "at={(1,0.5)}, anchor=base, rotate=180, yshift={0.375cm}") : PGFPlotsX.Options(),
            d == 4 && l == 256 ? PGFPlotsX.Options(:ylabel => "\$\\log_{10}\$ regret", :ylabel_style => "yshift={-0.5cm}") : PGFPlotsX.Options(),
            d == 8 && l == 1024 ? PGFPlotsX.Options(:xlabel => "Number of evaluations", :xlabel_style => "yshift={0.375cm}") : PGFPlotsX.Options(),
            d == 2 && l == 1024 ? PGFPlotsX.Options(:legend_entries => "{Dividing rectangles, Cholesky, Fourier feature, Random search, Approx. pathwise}") : PGFPlotsX.Options(),
        ),
        [Plot(
            merge(
                {
                    no_markers,
                    thick,
                }, 
                PGFPlotsX.Options(:color => color[c]),
                c == "random" && q == 0.5 ? PGFPlotsX.Options(:dashed => nothing) : PGFPlotsX.Options(),
                q == 0.5 ? PGFPlotsX.Options() : PGFPlotsX.Options(:draw => "none"),
                d == 2 && l == 1024 && q == 0.5 ? PGFPlotsX.Options() : PGFPlotsX.Options(:forget_plot => nothing),
                PGFPlotsX.Options(:name_path => "$(c)_$(Int(100*q))"),
            ),
            Coordinates(non_repeated_indices(dropdims(mapslices(a -> quantile(a, q), data[(d,l,c)], dims=1),dims=1))...),
        ) for c in ("direct","cholesky","rff","random","pathwise") for q in (0.25,0.5,0.75)]...,
        [Plot(
            merge(
                {
                    opacity = 0.125,
                    forget_plot,
                },
                PGFPlotsX.Options(:color => color[c]),
            ),
            "fill between [of = $(c)_75 and $(c)_25]",
        ) for c in ("direct","cholesky","rff","random","pathwise")]...,
    ) for d in (2,4,8) for l in (256,1024,4096)]...,
 ) |> TikzPicture |> save_tex("ts.tex")
