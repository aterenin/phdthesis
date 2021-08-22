using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true); push!(PGFPlotsX.CLASS_OPTIONS, "11pt")
using Colors
using Distributions
using Random
using LinearAlgebra: cholesky

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> picture -> PGFPlotsX.savetex("../figures/tex/$file", picture |> p -> TikzDocument("\\tikzsetnextfilename{$(replace(file, ".tex" => ""))}", p, use_default_preamble=false, preamble = preamble))

@eval(PGFPlotsX, PGFPlotsX.@define_axislike TikzFadingFromPicture "tikzfadingfrompicture")
using PGFPlotsX: TikzFadingFromPicture

function density_to_ellipse(distribution::AbstractMvNormal, num_points_per_contour::Int)
    angles = range(0, 2*pi, length = num_points_per_contour + 1)
    circle = hcat(cos.(angles),sin.(angles))
    return circle * cholesky(cov(distribution)).U
end

function density_to_patches(distribution::AbstractMvNormal, num_contours::Int, num_points_per_contour::Int)
    ellipse = density_to_ellipse(distribution, num_points_per_contour)
    radii = vcat(0, range(0, 3, length = num_contours + 1)[3:end], 30)
    ellipse_pairs = tuple.(eachcol(hcat(ellipse[1:end-1,:], ellipse[2:end,:]))...)
    radius_pairs = tuple.(eachcol(hcat(radii[1:end-1], radii[2:end]))...)
    rectangles = Tuple[]
    for (r1,r2) in radius_pairs
        for (x1,y1,x2,y2) in ellipse_pairs
            push!(rectangles, (r1 .* (x1,y1)))
            push!(rectangles, (r2 .* (x1,y1)))
            push!(rectangles, (r2 .* (x2,y2)))
            push!(rectangles, (r1 .* (x2,y2)))
        end
    end
    xyc = hcat([[x,y,pdf(distribution,[x,y])] for (x,y) in rectangles]...)
    xyc[abs.(xyc) .< 0.005] .= 0
    return Table([:x => xyc[1,:], :y => xyc[2,:], :c => xyc[3,:]])
end



m = [0., 0.]
K = [1. -0.9; 
    -0.9 1.]
joint = MvNormal(m,K)

y_cond = -1
m_cond = m[1] + K[1,2] * K[2,2]^-1 * (y_cond - m[2])
K_cond = K[1,1] - K[1,2] * K[2,2]^-1 * K[2,1]
cond = Normal(m_cond, sqrt(K_cond))

x = -3:0.1:3
density_cond = [pdf(cond, a) for a in x]
Random.seed!(1)
samples_cond = rand(cond, 250)



for (dist,name) in ((MvNormal(m, [1. 0.6; 0.6 1]),"mvn-pos"),(joint,"mvn-neg"),(joint,"mvn-dist-joint"))
    @pgf [raw"\tikzexternaldisable",
        TikzFadingFromPicture(
            {
                name = "densityfade"
            },
            Axis(
                {
                    axis_lines = "none",
                    height = "3.375cm",
                    width = "3.375cm",
                    xmin=-3, xmax=3, ymin=-3, ymax=3,
                    clip_mode="individual",
                },
                Plot(
                    { 
                        patch,
                        patch_type = "rectangle",
                        point_meta = raw"\thisrow{c}",
                        shader = "interp",
                        colormap="{blackwhite}{gray(0cm)=(0); gray(1cm)=(0.75)}",
                    },
                    density_to_patches(dist, 12, 48)
                ),
            )
        ), 
        raw"\tikzexternalenable",
        TikzPicture(
            Axis(
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
            [raw"\fill", {
                path_fading = "densityfade",
                fill = colorant"#1f77b4",
                fit_fading = true,
            }, raw"(-3,-3) rectangle (3,3);"],
            if name=="mvn-dist-joint" HLine(
                { 
                    black,
                    ultra_thick,
                }, 
                y_cond
            ) else [] end,
            [raw"\draw", {
                draw="none",
                fill=colorant"#1f77b4",
                fill_opacity=0.5
            }, "(0,0) circle (1.6pt);"],
            [Plot(
                {
                    no_markers,
                    smooth,
                    ultra_thick,
                    color=colorant"#1f77b4",
                    opacity=0.5,
                },
                Coordinates(radius .* density_to_ellipse(dist, 48)[:,1], radius .* density_to_ellipse(dist, 48)[:,2])
            ) for radius in [quantile(Normal(0,1),0.8),quantile(Normal(0,1),0.95),quantile(Normal(0,1),0.99)]]...
        )
    )] |> save_tex("$name.tex")
end


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
) |> TikzPicture |> save_tex("mvn-dist-cond.tex")
