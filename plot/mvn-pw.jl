using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true); push!(PGFPlotsX.CLASS_OPTIONS, "11pt")
using Colors
using Distributions
using Random
using KernelDensity

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> axis -> PGFPlotsX.savetex("../figures/tex/$file", axis |> TikzPicture |> p -> TikzDocument("\\tikzsetnextfilename{figures/tex/$(replace(file, ".tex" => ".pdf"))}", p, use_default_preamble=false, preamble = preamble))



m = [0., 0.]
K = [1. -0.9; 
    -0.9 1.]
joint = MvNormal(m,K)
Random.seed!(1)
samples_joint = rand(joint, 500)

y_cond = -1
m_cond = m[1] + K[1,2] * K[2,2]^-1 * (y_cond - m[2])
K_cond = K[1,1] - K[1,2] * K[2,2]^-1 * K[2,1]
cond = Normal(m_cond, sqrt(K_cond))

x = -3:0.1:3
density_cond = [pdf(cond, a) for a in x]
samples_cond = samples_joint[1,1:250] + K[1,2] * K[2,2]^-1 * (y_cond .- samples_joint[2,1:250])
kde_cond = kde(samples_cond, x)

highlight_joint = [-1.25,1]
highlight_cond = highlight_joint[1] + K[1,2] * K[2,2]^-1 * (y_cond .- highlight_joint[2])



@pgf Axis(
    {
        axis_lines = "none",
        height = "6.5cm",
        width = "6.5cm",
        xmin=-3, xmax=3, ymin=-3, ymax=3,
        clip_mode="individual",
    },
    [raw"\node at (-3,-3) {};"],
    [raw"\node at (-3,3) {};"],
    [raw"\node at (3,3) {};"],
    [raw"\node at (3,-3) {};"],
    Plot(
        { 
            only_marks,
            color=colorant"#1f77b4",
            opacity = 0.25,
        },
        Coordinates(samples_joint[1,:],samples_joint[2,:])
    ),
    HLine(
        { 
            black,
            ultra_thick,
        }, 
        y_cond
    ),
    Plot(
        { 
            only_marks,
            mark_size="3pt",
            fill=colorant"#ff7f0e",
        },
        Coordinates([highlight_joint[1]], [highlight_joint[2]])
    ),
) |> save_tex("mvn-pw-joint.tex")



@pgf Axis(
    {
        axis_lines = "none",
        height = "6.5cm",
        width = "6.5cm",
        xmin=-3, xmax=3, ymin=-3, ymax=3,
        clip_mode="individual",
    },
    [raw"\node at (-3,-3) {};"],
    [raw"\node at (-3,3) {};"],
    [raw"\node at (3,3) {};"],
    [raw"\node at (3,-3) {};"],
    Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colorant"#1f77b4",
            fill=colorant"#1f77b4",
            fill_opacity = 0.25,
        },
        Coordinates(kde_cond.x, y_cond .+ kde_cond.density)
    ),
    Plot(
        {
            no_markers,
            smooth,
            black,
            very_thick,
            dashed,
        },
        Coordinates(x, y_cond .+ density_cond)
    ),
    HLine(
        { 
            black,
            ultra_thick,
        }, 
        y_cond
    ),
    Plot(
        { 
            only_marks,
            mark="|",
            mark_size="3.5pt",
            color=colorant"#1f77b4",
            opacity = 0.5,
        },
        Coordinates(samples_cond,fill(y_cond,length(samples_cond)))
    ),
    Plot(
        {
            no_markers,
            dashed,
            black,
            thick,
        },
        Coordinates([tuple(highlight_joint...),(highlight_cond,highlight_joint[2]),(highlight_cond,y_cond)])
    ),
    Plot(
        { 
            only_marks,
            mark="|",
            mark_size="3.5pt",
            ultra_thick,
            color=colorant"#ff7f0e",
        },
        Coordinates([highlight_cond], [y_cond])
    ),
    Plot(
        {
            quiver = {u = raw"\thisrow{u}", v = raw"\thisrow{v}"},
            very_thick,
            "-latex"
        },
        Table(x = [highlight_joint[1]], y = [highlight_joint[2]], u = 0.99.*[highlight_cond - highlight_joint[1]], v = 0.99.*[y_cond - highlight_joint[2]])
    ),
    Plot(
        { 
            only_marks,
            mark_size="3pt",
            fill=colorant"#ff7f0e",
        },
        Coordinates([highlight_joint[1]], [highlight_joint[2]])
    ),
) |> save_tex("mvn-pw-cond.tex")
