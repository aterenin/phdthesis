using PGFPlotsX

@eval(PGFPlotsX, _OLD_LUALATEX = true)
@eval(PGFPlotsX, CLASS_OPTIONS = ["tikz","11pt"])

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{amssymb}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex(file; extra = "") = picture -> PGFPlotsX.savetex("../figures/tex/$file", TikzDocument(chomp("\\tikzsetnextfilename{$(replace(file, ".tex" => ""))}\n$(extra)"), picture, use_default_preamble=false, preamble = preamble))
color_to_pgf(rgb) = "{rgb,1:red,$(round(rgb.r, digits=4));green,$(round(rgb.g, digits=4));blue,$(round(rgb.b, digits=4))}"
colorscheme_to_pgf(name) = "{" * name * "}{" * join(map(rgb -> "rgb=($(rgb.r),$(rgb.g),$(rgb.b))", getproperty(ColorSchemes, Symbol(name))), "\n") * "}"
legend_entry(pair) = ["\\addlegendimage{$(pair[1])}\n\\addlegendentry{$(pair[2])}"]

function non_repeated_indices(v)
    d = findall(diff(v) .!= 0)
    idxs = sort(unique(vcat(1, d, d .+ 1, length(v))))
    (idxs, v[idxs])
end