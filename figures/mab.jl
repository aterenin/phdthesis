using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true)
using Colors
using Distributions
using Random

preamble = [raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex(file, axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{figures/$(replace(file, ".tex" => ".pdf"))}", p, use_default_preamble=false, preamble = preamble))

function condition(prior, likelihood, data)
    map(enumerate(data)) do (i,y)
        s = (1/var(prior) + length(y)/var(likelihood(i)))^-1
        m = s * (mean(prior)/var(prior) + sum(y)/var(likelihood(i)))
        Normal(m,s)
    end
end 

function get_ucb(distributions, time)
    means = map(d -> mean(d), distributions)
    vars = map(d -> var(d), distributions)
    constant = 2*log(time)
    means .+ sqrt.(constant .* vars)
end

dist_1 = Normal(0, 1)
dist_2 = Normal(0.75, 0.75)
dist_3 = Normal(0.5, 1.25)

x = vcat(-3,-3:0.25:3,3)
z = min(x...):0.05:max(x...)

pdf_boundary = vcat(0,ones(length(x)-2),0)
pdf_1 = [pdf(dist_1, a) for a in x] .* pdf_boundary
pdf_2 = [pdf(dist_2, a) for a in x] .* pdf_boundary
pdf_3 = [pdf(dist_3, a) for a in x] .* pdf_boundary

Random.seed!(2)
samples_1 = rand(dist_1,5)
samples_2 = rand(dist_2,4)
samples_3 = rand(dist_3,6)

density = [pdf_1,pdf_2,pdf_3]
samples = [samples_1, samples_2, samples_3]
dist = [dist_1, dist_2, dist_3]

prior = Normal(0,1)
likelihood = i -> dist[i]
posterior = condition(prior, likelihood, samples)
posterior_density_scaling_factor = 0.234375
posterior_density = [[posterior_density_scaling_factor * pdf(p,a) for a in z] for p in posterior]
ucb = get_ucb(posterior, length(samples_1) + length(samples_2) + length(samples_3))

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
    [raw"\begin{scope}", {
        transparency_group, 
        opacity=0.25
    }],
    [raw"\clip(-1.5,-3) rectangle (1.5,3);"],
    [[raw"\draw", {
        ultra_thick,
        draw=colorant"#1f77b4",
    }, 
    "plot coordinates {",
    join(string.(zip((-1:1:1)[i] .+ [0, max(density[i]...)], fill(mean(dist[i]),2))), "  "),
    "};"] for i in 1:3]...,
    [[raw"\draw", {
        ultra_thick,
        draw=colorant"#1f77b4",
        fill=colorant"#1f77b4",
        fill_opacity = 0.5,
    }, 
    "plot [smooth] coordinates {",
    join(string.(zip((-1:1:1)[i] .+ density[i], x)), "  "), 
    "};"] for i in 1:3]...,
    [raw"\end{scope}"],
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
) |> save_tex("tex/mab-samples.tex")


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
        Coordinates((-1:1:1)[i] .+ posterior_density[i], z)
    ) for i in 1:3]...,
    [VLine(
        { 
            black,
            very_thick,
        }, 
        i
    ) for i in -1:1:1]...,
) |> save_tex("tex/mab-post.tex")


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
            ultra_thick,
            color=colorant"#1f77b4",
        },
        Coordinates([((-1:1:1)[i] - 1/3, ucb[i]), ((-1:1:1)[i] + 1/3, ucb[i])])
    ) for i in 1:3]...,
) |> save_tex("tex/mab-ucb.tex")