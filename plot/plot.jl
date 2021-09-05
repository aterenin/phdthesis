using PGFPlotsX

@eval(PGFPlotsX, _OLD_LUALATEX = true)
@eval(PGFPlotsX, CLASS_OPTIONS = ["tikz","11pt"])

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{amssymb}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex(file) = picture -> PGFPlotsX.savetex("../figures/tex/$file", picture |> p -> TikzDocument("\\tikzsetnextfilename{$(replace(file, ".tex" => ""))}", p, use_default_preamble=false, preamble = preamble))
colorscheme_to_pgf(name) = "{" * name * "}{" * join(map(rgb -> "rgb=($(rgb.r),$(rgb.g),$(rgb.b))", getproperty(ColorSchemes, Symbol(name))), "\n") * "}"

function non_repeated_indices(v)
    d = findall(diff(v) .!= 0)
    idxs = sort(unique(vcat(1, d, d .+ 1, length(v))))
    (idxs, v[idxs])
end