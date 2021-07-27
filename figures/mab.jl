using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true)
using Colors
using Distributions
using Random

preamble = [raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex(file, axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{figures/$(replace(file, ".tex" => ".pdf"))}", p, use_default_preamble=false, preamble = preamble))

dist_1 = Normal(0, 1)
dist_2 = Normal(0.75, 0.75)
dist_3 = Normal(0.5, 1.25)

x = -3:0.25:3

pdf_1 = [pdf(dist_1, a) for a in x]
pdf_2 = [pdf(dist_2, a) for a in x]
pdf_3 = [pdf(dist_3, a) for a in x]

Random.seed!(2)
samples_1 = rand(dist_1,5)
samples_2 = rand(dist_2,4)
samples_3 = rand(dist_3,6)

density = [pdf_1,pdf_2,pdf_3]
samples = [samples_1, samples_2, samples_3]
dist = [dist_1, dist_2, dist_3]

@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "4cm",
        xmin=-1.5, xmax=1.5, ymin=-3, ymax=3,
        clip_mode="individual",
        
    },
    [raw"\node at (-1.5,-3) {};"],
    [raw"\node at (1.5,-3) {};"],
    [raw"\node at (1.5,3) {};"],
    [raw"\node at (-1.5,3) {};"],
    [Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colorant"#1f77b4",
            fill=colorant"#1f77b4",
            fill_opacity = 0.25,
        },
        Coordinates([((-1:1.:1)[i], mean(dist[i])), ((-1:1.:1)[i] + max(density[i]...), mean(dist[i]))])
    ) for i in 1:3]...,
    [Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colorant"#1f77b4",
            fill=colorant"#1f77b4",
            fill_opacity = 0.25,
        },
        Coordinates((-1:1:1)[i] .+ density[i], x)
    ) for i in 1:3]...,
    [VLine(
        { 
            black,
            very_thick,
        }, 
        i
    ) for i in -1:1:1]...,
) |> save_tex("tex/mab-dist.tex")

@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "4cm",
        xmin=-1.5, xmax=1.5, ymin=-3, ymax=3,
        clip_mode="individual",
        
    },
    [raw"\node at (-1.5,-3) {};"],
    [raw"\node at (1.5,-3) {};"],
    [raw"\node at (1.5,3) {};"],
    [raw"\node at (-1.5,3) {};"],
    [VLine(
        { 
            black,
            very_thick,
        }, 
        i
    ) for i in -1:1:1]...,
    [Plot(
        {
            only_marks,
            color=colorant"#1f77b4",
        },
        Coordinates(fill((-1:1.:1)[i], length(samples[i])), samples[i])
    ) for i in 1:3]...,
) |> save_tex("tex/mab-data.tex")

@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "4cm",
        xmin=-1.5, xmax=1.5, ymin=-3, ymax=3,
        clip_mode="individual",
        
    },
    [raw"\node at (-1.5,-3) {};"],
    [raw"\node at (1.5,-3) {};"],
    [raw"\node at (1.5,3) {};"],
    [raw"\node at (-1.5,3) {};"],
    [VLine(
        { 
            black,
            very_thick,
        }, 
        i
    ) for i in -1:1:1]...,
    [Plot(
        {
            no_markers,
            color=colorant"#1f77b4",
            line_width = "4pt",
        },
        Coordinates([((-1:1.:1)[i], mean(dist[2])), ((-1:1.:1)[i], mean(dist[i]))])
    ) for i in 1:3]...,
    [Plot(
        {
            only_marks,
            color=colorant"#1f77b4",
            mark = "-",
            mark_size = "4pt",
            very_thick,
        },
        Coordinates([((-1:1.:1)[i], mean(dist[2])), ((-1:1.:1)[i], mean(dist[i]))])
    ) for i in 1:3]...,
) |> save_tex("tex/mab-regret.tex")