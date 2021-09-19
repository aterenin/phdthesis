using ColorSchemes
using DelimitedFiles

color_as_matrix(a) = hcat(map(c->[c.r,c.g,c.b], a)...)

writedlm("../results/col/viridis.csv",  color_as_matrix(ColorSchemes.viridis.colors), ", ")
writedlm("../results/col/plasma.csv",  color_as_matrix(ColorSchemes.plasma.colors), ", ")