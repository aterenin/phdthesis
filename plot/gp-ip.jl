include("plot.jl")
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

z = 0.4:0.05:0.7
u = zeros(length(z))
d = 0.4:0.01:0.7
y = zeros(length(d))
x = 0:0.0125:1
a = 0.1
ls = 0.15
k = a * with_lengthscale(Matern52Kernel(), ls)
s = 0.000001
l = 32
L = length(z)

idx_z = [findfirst(v -> v==w, x) for w in z]

K_xx = kernelmatrix(k, x, x)
K_xz = kernelmatrix(k, x, z)
K_zz = kernelmatrix(k, z, z)
K_dz = kernelmatrix(k, d, z)
K_xd = kernelmatrix(k, x, d)
K_dd = kernelmatrix(k, d, d)

m_cond = K_xz * ((K_zz + s*I) \ u)
K_cond = Symmetric(K_xx - K_xz * ((K_zz + s*I) \ K_xz'))

Random.seed!(4)
dist_joint = MvNormal(zeros(length(x)), K_xx)
samples_joint = rand(dist_joint, l)

dist_inducing = MvNormal(zeros(length(z)), Symmetric(K_zz * (K_zz + K_dz' * K_dz / s^2) \ K_zz) )
samples_inducing = rand(dist_inducing, l)

samples_cond = samples_joint + K_xz * (K_zz \ (samples_inducing .- samples_joint[idx_z,:]))
samples_canonical = K_xz * (K_zz \ (samples_inducing .- samples_joint[idx_z,:]))

m_exact = K_xd * ((K_dd + s*I) \ y)
K_exact = Symmetric(K_xx - K_xd * ((K_dd + s*I) \ K_xd'))
dist_exact = MvNormal(m_exact, K_exact)
samples_exact = rand(dist_exact, l)

colors = range(weighted_color_mean(2/3, colorant"#1f77b4",colorant"white"), weighted_color_mean(2/3, colorant"#1f77b4",colorant"black"); length=L)



for (f,m,K,name) in ((samples_exact,m_exact,K_exact,"gp-ex-cond"),(samples_cond,m_cond,K_cond,"gp-ip-cond"))
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
        Plot(
            {
                no_markers,
                smooth,
                very_thick,
                color=colorant"#1f77b4",
                name_path = "upper",
            },
            Coordinates(x, m + 1.96*sqrt.(diag(K)))
        ),
        Plot(
            {
                no_markers,
                smooth,
                very_thick,
                color=colorant"#1f77b4",
                name_path = "lower",
            },
            Coordinates(x, m - 1.96*sqrt.(diag(K)))
        ),
        Plot(
            {
                color=colorant"#1f77b4",
                opacity = 0.25
            },
            raw"fill between [of = upper and lower]",
        ),
        Plot(
            {
                no_markers,
                smooth,
                ultra_thick,
                color=colorant"#1f77b4",
            },
            Coordinates(x, m)
        ),
        [Plot(
            {
                no_markers,
                smooth,
                thick,
                color=colorant"#1f77b4",
                opacity = 0.5
            },
            Coordinates(x, f[:,i])
        ) for i in 1:l]...,
        if name == "gp-ex-cond" 
            Plot(
                { 
                    only_marks,
                    mark="|",
                    mark_size="2pt",
                    thick,
                    color=colorant"#1f77b4",
                },
                Coordinates(d, y)
            ) 
        elseif name == "gp-ip-cond" 
            Plot(
                { 
                    only_marks,
                    thick,
                    fill=weighted_color_mean(0.875,colorant"#ffffff",colorant"#1f77b4"),
                },
                Coordinates(z, u)
            ) 
        end,
    ) |> TikzPicture |> save_tex("$name.tex")
end

@pgf Axis(
    {
        axis_lines = "none",
        height = "5cm",
        width = "6.5cm",
        xmin=0, xmax=1, ymin=-0.1, ymax=0.2,
    },
    [raw"\node at (0,-0.1) {};"],
    [raw"\node at (0,0.2) {};"],
    [raw"\node at (1,0.2) {};"],
    [raw"\node at (1,-0.1) {};"],
    [Plot(
        {
            no_markers,
            smooth,
            ultra_thick,
            color=colors[i],
        },
        Coordinates(x, K_xz[:,(1:L)[i]])
    ) for i in 1:L]...,
) |> TikzPicture |> save_tex("gp-ip-basis.tex")



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
            smooth,
            thick,
            color=colorant"#1f77b4",
            opacity = 0.5
        },
        Coordinates(x, samples_canonical[:,i])
    ) for i in 1:l]...,
) |> TikzPicture |> save_tex("gp-ip-samples.tex")

extra_mark = raw"\pgfdeclareplotmark{|||}{\pgfpathmoveto{\pgfqpoint{-2pt}{\pgfplotmarksize}}\pgfpathlineto{\pgfqpoint{-2pt}{-\pgfplotmarksize}}\pgfpathmoveto{\pgfqpoint{0pt}{\pgfplotmarksize}}\pgfpathlineto{\pgfqpoint{0pt}{-\pgfplotmarksize}}\pgfpathmoveto{\pgfqpoint{2pt}{\pgfplotmarksize}}\pgfpathlineto{\pgfqpoint{2pt}{-\pgfplotmarksize}}\pgfusepathqstroke}"

@pgf Axis(
    {
        hide_axis,
        xmin = 0,
        xmax = 1,
        ymin = 0,
        ymax = 1,
        legend_columns = -1, 
        legend_style = raw"draw={none}, legend cell align={center}, font={\footnotesize}, column sep={0.0625cm}, /tikz/every even column/.append style={column sep=0.375cm}",
    },
    legend_entry("only marks, mark={|||}, mark size={2pt}, color=$(color_to_pgf(colorant"#1f77b4"))" => "Data"),
    legend_entry("only marks, mark options={thick}, mark={*}, fill=$(color_to_pgf(weighted_color_mean(0.875,colorant"#ffffff",colorant"#1f77b4")))" => "Inducing points"),
    legend_entry("opacity={0.5}, thick, color=$(color_to_pgf(colorant"#1f77b4"))" => "Samples"),
) |> TikzPicture |> save_tex("gp-ip-lgnd.tex", extra=extra_mark)