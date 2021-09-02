using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true); push!(PGFPlotsX.CLASS_OPTIONS, "11pt")
using Colors
using ColorSchemes
using DelimitedFiles
using Statistics

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> picture -> PGFPlotsX.savetex("../figures/tex/$file", picture |> p -> TikzDocument("\\tikzsetnextfilename{$(replace(file, ".tex" => ""))}", p, use_default_preamble=false, preamble = preamble))

colorscheme_to_pgf(name) = "{" * name * "}{" * join(map(rgb -> "rgb=($(rgb.r),$(rgb.g),$(rgb.b))", getproperty(ColorSchemes, Symbol(name))), "\n") * "}"


xy = readdlm("../results/ggp/ggp_xy.csv", ',')
mean = readdlm("../results/ggp/ggp_mean.csv", ',') |> vec
std = readdlm("../results/ggp/ggp_std.csv", ',') |> vec
idxs = readdlm("../results/ggp/ggp_data.csv", ',', Int) |> vec


for name in ("ggp-mean","ggp-std")
    @pgf Axis(
            {
                axis_lines = "none",
                height = "8.25cm",
                width = "8.25cm",
            },
            [raw"\node[inner sep=0pt] (a) at (-121.949,37.331) {\phantom{\includegraphics[scale=0.5]{figures/png/map}}};"],
            [raw"\clip[rounded corners=0.15cm] (a.south west) rectangle (a.north east);"],
            [raw"\node at (a.center) {\includegraphics[scale=0.5]{figures/png/map}};"],
            Plot(
                { 
                    only_marks,
                    scatter,
                    scatter_src="explicit",
                    colormap = name == "ggp-std" ? colorscheme_to_pgf("viridis") : colorscheme_to_pgf("plasma"),
                    mark_size="2.5pt",
                    opacity=0.5,
                },
                Table(
                    {
                        meta = "color",
                    },
                    x = xy[:,1],
                    y = xy[:,2],
                    color = name == "ggp-std" ? clamp.(std, 0, 10) : mean,
                ),
            ),
            Plot(
                { 
                    only_marks,
                    draw="none",
                    fill="white",
                    mark_size="1.125pt",
                    opacity=0.5,
                    draw_opacity = 0,
                },
                Coordinates(xy[idxs,1],xy[idxs,2])
            ),
        ) |> TikzPicture |> save_tex("$name.tex")
end




for name in ("ggp-mean-zoom","ggp-std-zoom")
    @pgf Axis(
            {
                axis_lines = "none",
                height = "7.5cm",
                width = "6.9cm",
                xmin=-121.901,
                xmax=-121.884,
                ymin=37.315,
                ymax=37.33,
            },
            [raw"\node[inner sep=0pt] (a) at (-121.8925,37.3231) {\phantom{\includegraphics[scale=0.5]{figures/png/map_zoom}}};"],
            [raw"\clip[rounded corners=0.15cm] (a.south west) rectangle (a.north east);"],
            [raw"\node at (a.center) {\includegraphics[scale=0.5]{figures/png/map_zoom}};"],
            Plot(
                { 
                    only_marks,
                    scatter,
                    scatter_src="explicit",
                    colormap = name == "ggp-std-zoom" ? colorscheme_to_pgf("viridis") : colorscheme_to_pgf("plasma"),
                    mark_size="4pt",
                    opacity=0.875,
                },
                Table(
                    {
                        meta = "color",
                    },
                    x = xy[:,1],
                    y = xy[:,2],
                    color = name == "ggp-std-zoom" ? clamp.(std, 0, 10) : mean,
                ),
            ),
            Plot(
                { 
                    only_marks,
                    draw="none",
                    fill="white",
                    mark_size="1.75pt",
                    opacity=0.875,
                    draw_opacity = 0,
                },
                Coordinates(xy[idxs,1],xy[idxs,2])
            ),
        ) |> TikzPicture |> save_tex("$name.tex")
end


