include("plot.jl")
using Colors
using DelimitedFiles
using Statistics

data = Dict((t,m,f,k) => readdlm("../results/gabo/$(t)_regret_$(m)_$(f)_$(k).csv", ',') for t in ("eubo","gabo") for m in ("s3","s5","so3") for f in ("a","r","l") for k in ("sqe","m25"))
color = Dict(("gabo","sqe") => colorant"#ff7f0e", ("gabo","m25") => colorant"#1f77b4", ("eubo","sqe") => weighted_color_mean(0.25, colorant"#000000", colorant"#ff7f0e"), ("eubo","m25") => weighted_color_mean(0.25, colorant"#000000", colorant"#1f77b4"))

@pgf GroupPlot(
    {
        group_style = { 
            group_size = "3 by 3",
            horizontal_sep = "1.5cm",
            vertical_sep = "1cm",
        },
    },
    [Axis(
        merge(
            {
                height = "5.375cm",
                width = "5.375cm",
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
                legend_columns = 2, 
                legend_style = raw"draw=none, fill=none, at={(0.5,1.2)}, anchor=south, font={\footnotesize}, /tikz/every even column/.append style={column sep=0.25cm}",
                xtick = "1,50,100,150,200",
                yticklabel_style = raw"/pgf/number format/frac",
            },
            f == "r" ? PGFPlotsX.Options() : PGFPlotsX.Options(:xtick_style => "draw=none", :xticklabels => ",,", :x_axis_line_style => "draw=none"),
            f == "a" && m == "s3" ? PGFPlotsX.Options(:ymin => -2, :ymax => 1) : PGFPlotsX.Options(),
            f == "a" && m == "s5" ? PGFPlotsX.Options(:ymin => -1.5, :ymax => 0.5) : PGFPlotsX.Options(),
            f == "a" && m == "so3" ? PGFPlotsX.Options(:ymin => -2, :ymax => 1) : PGFPlotsX.Options(),
            f == "r" && m == "s3" ? PGFPlotsX.Options(:ymin => 0, :ymax => 2) : PGFPlotsX.Options(),
            f == "r" && m == "s5" ? PGFPlotsX.Options(:ymin => 1, :ymax => 2.5) : PGFPlotsX.Options(),
            f == "r" && m == "so3" ? PGFPlotsX.Options(:ymin => 1.5, :ymax => 3.5) : PGFPlotsX.Options(),
            f == "l" && m == "s3" ? PGFPlotsX.Options(:ymin => -1, :ymax => 0, :ytick => "-1,-0.75,-0.5,-0.25,0") : PGFPlotsX.Options(),
            f == "l" && m == "s5" ? PGFPlotsX.Options(:ymin => -0.5, :ymax => 0.5, :ytick => "-0.5,-0.25,0,0.25,0.5") : PGFPlotsX.Options(),
            f == "l" && m == "so3" ? PGFPlotsX.Options(:ymin => 0.9375, :ymax => 1.1875, :ytick => "0.9375,1,1.0625,1.125,1.1875", :yticklabels => raw"\ensuremath{\frac{15}{16}},\ensuremath{1},\ensuremath{1\frac{1}{16}},\ensuremath{1\frac{1}{8}},\ensuremath{1\frac{3}{16}}") : PGFPlotsX.Options(),
            f == "a" ? PGFPlotsX.Options(:title => if m=="s3" raw"$\mathbb{S}^3$" elseif m=="s5" raw"$\mathbb{S}^5$" elseif m=="so3" raw"$SO(3)$" end) : PGFPlotsX.Options(),
            m == "so3" ? PGFPlotsX.Options(:ylabel => if f=="a" "Ackley" elseif f=="r" "Rosenbrock" elseif f=="l" "Levy" end) : PGFPlotsX.Options(),
            m == "so3" ? PGFPlotsX.Options(:ylabel_style => "at={(1,0.5)}, anchor=base, rotate=180, yshift={0.375cm}") : PGFPlotsX.Options(),
            f == "l" && m == "s3" ? PGFPlotsX.Options(:ylabel => "\$\\log_{10}\$ regret", :ylabel_style => "yshift={-0.5cm}") : PGFPlotsX.Options(),
            f == "r" && m == "s5" ? PGFPlotsX.Options(:xlabel => "Number of evaluations", :xlabel_style => "yshift={0.375cm}") : PGFPlotsX.Options(),
            f == "a" && m == "s5" ? PGFPlotsX.Options(:legend_entries => "{Euclidean Squared Exponential, Euclidean Matérn-5/2, Riemannian Squared Exponential, Riemannian Matérn-5/2}") : PGFPlotsX.Options(),
        ),
        [Plot(
            merge(
                {
                    no_markers,
                    thick,
                }, 
                PGFPlotsX.Options(:color => color[(t,k)]),
                t == "eubo" && q == 0.5 ? PGFPlotsX.Options(:dashed => nothing) : PGFPlotsX.Options(),
                q == 0.5 ? PGFPlotsX.Options() : PGFPlotsX.Options(:draw => "none"),
                f == "a" && m == "s5" && q == 0.5 ? PGFPlotsX.Options() : PGFPlotsX.Options(:forget_plot => nothing),
                PGFPlotsX.Options(:name_path => "$(t)_$(k)_$(Int(100*q))"),
            ),
            Coordinates(non_repeated_indices(dropdims(mapslices(a -> quantile(a, q), data[(t,m,f,k)], dims=1),dims=1))...),
        ) for t in ("eubo","gabo") for k in ("sqe","m25") for q in (0.25,0.5,0.75)]...,
        [Plot(
            merge(
                {
                    opacity = 0.125,
                    forget_plot,
                },
                PGFPlotsX.Options(:color => color[(t,k)]),
            ),
            "fill between [of = $(t)_$(k)_75 and $(t)_$(k)_25]",
        ) for t in ("eubo","gabo") for k in ("sqe","m25")]...,
    ) for f in ("a","l","r") for m in ("s3","s5","so3")]...,
 ) |> TikzPicture |> save_tex("gabo.tex")
