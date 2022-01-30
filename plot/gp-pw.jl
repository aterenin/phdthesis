include("plot.jl")
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

z = [0.5,0.75]
u = [0.15,-0.15]
x = 0:0.0125:1
a = 0.1
ls = 0.1
k = a * with_lengthscale(Matern52Kernel(), ls)
s = 0.01
l = 32

idx_z = [findfirst(v -> v==w, x) for w in z]

K_xx = kernelmatrix(k, x, x)
K_xz = kernelmatrix(k, x, z)
K_zz = kernelmatrix(k, z, z)

m_cond = K_xz * ((K_zz + s*I) \ u)
K_cond = Symmetric(K_xx - K_xz * ((K_zz + s*I) \ K_xz'))

Random.seed!(5)
dist_prior = MvNormal(zeros(length(x)), K_xx)
samples_prior = rand(dist_prior, l) 
dist_noise = MvNormal(zeros(length(z)), s*I)
samples_noise = rand(dist_noise, l)

samples_cond = samples_prior + K_xz * ((K_zz + s*I) \ (u .- samples_prior[idx_z,:] .- samples_noise))

for (f,m,K,name) in ((samples_prior, zeros(length(x)), K_xx, "gp-pw-prior"),(samples_cond, m_cond, K_cond, "gp-pw-cond"))
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
            Coordinates(x, m .+ 1.96*sqrt.(diag(K)))
        ),
        Plot(
            {
                no_markers,
                smooth,
                very_thick,
                color=colorant"#1f77b4",
                name_path = "lower",
            },
            Coordinates(x, m .- 1.96*sqrt.(diag(K)))
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
        ) for i in 1:size(f, 2)]...,
        Plot(
            { 
                only_marks,
                mark_size="3pt",
                very_thick,
                fill=weighted_color_mean(0.875,colorant"#ffffff",colorant"#1f77b4"),
            },
            Coordinates(z, u)
        ),
    ) |> TikzPicture |> save_tex("$name.tex")
end