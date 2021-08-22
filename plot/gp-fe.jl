using PGFPlotsX; @eval(PGFPlotsX, _OLD_LUALATEX = true); push!(PGFPlotsX.CLASS_OPTIONS, "11pt")
using Colors
using Random
using SparseArrays
using LinearAlgebra: cholesky

preamble = [raw"\usepackage{lmodern}", raw"\usepackage{pgfplots}", raw"\pgfplotsset{compat=1.17}", raw"\usepgfplotslibrary{external}", raw"\usepgfplotslibrary{groupplots}", raw"\usepgfplotslibrary{fillbetween}", raw"\usetikzlibrary{fadings}"]
save_tex = file -> picture -> PGFPlotsX.savetex("../figures/tex/$file", picture |> p -> TikzDocument("\\tikzsetnextfilename{$(replace(file, ".tex" => ""))}", p, use_default_preamble=false, preamble = preamble))

function assemble_matrices(x::AbstractVector)
    n = length(x)
    A = spzeros(n,n)
    M = spzeros(n,n)
    for i in 1:length(x)
        for j in 1:length(x)
            if i == j 
                vol = x[min(n,i+1)] - x[max(1,i-1)]
                if i==1 || i == length(x)
                    A[i,j] = 1/vol
                else
                    A[i,j] = 4/vol
                end
                M[i,j] = vol/3
            elseif abs(i - j) == 1
                vol = x[max(i,j)] - x[min(i,j)]
                A[i,j] = -1/vol
                M[i,j] = vol/6
            end
        end
    end
    (A,M)
end


x = 0:0.1:1
a = 15
ls = 0.2
l = 256
n = 32

(N,M) = assemble_matrices(x)
A = 3/ls^2 * M + N

Random.seed!(3)
w = a * (A \ (sparse(cholesky(M).L) * randn(length(x), n)))

colors = range(weighted_color_mean(1/2, colorant"#1f77b4",colorant"white"), weighted_color_mean(1/2, colorant"#1f77b4",colorant"black"); length=length(x))
color_idx = [1, 3, 6, 9, 4, 7, 10, 5, 8, 11, 2]

@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=0, xmax=1, ymin=-0.75, ymax=1.75,
    },
    [raw"\node at (0,-2.5) {};"],
    [raw"\node at (0,2.5) {};"],
    [raw"\node at (1,2.5) {};"],
    [raw"\node at (1,-2.5) {};"],
    Plot(
        {
            no_markers,
            ultra_thick,
            color=colors[color_idx[1]],
        },
        Coordinates([(x[1],1),(x[2],0)])
    ),
    [Plot(
        {
            no_markers,
            ultra_thick,
            color=colors[color_idx[i]],
        },
        Coordinates([(x[i-1],0),(x[i],1),(x[i+1],0)])
    ) for i in 2:length(x)-1]...,
    Plot(
        {
            no_markers,
            ultra_thick,
            color=colors[color_idx[end]],
        },
        Coordinates([(x[end-1],0),(x[end],1)])
    ),
) |> TikzPicture |> save_tex("gp-fe-basis.tex")



@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=0, xmax=1, ymin=-1, ymax=1,
    },
    [raw"\node at (0,-1) {};"],
    [raw"\node at (0,1) {};"],
    [raw"\node at (1,1) {};"],
    [raw"\node at (1,-1) {};"],
    [Plot(
        {
            no_markers,
            thick,
            color=colorant"#1f77b4",
            opacity = 0.5
        },
        Coordinates(x, w[:,i])
    ) for i in 1:n]...,
) |> TikzPicture |> save_tex("gp-fe-samples.tex")
