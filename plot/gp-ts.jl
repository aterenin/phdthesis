include("plot.jl")
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

x =  -0.5:0.01:0.5
a = 0.1
ls = 0.1
s = 0.00001

l = 1024
n = 1

k = a * with_lengthscale(SqExponentialKernel(), ls)
K(x1,x2) = kernelmatrix(k, x1, x2)

f_cond(x,z,u,w,e) = length(z) == 0 ? f(x,w) : f(x,w) + K(x,z) * ((K(z,z) + s*I) \ (u .- f(z,w) .- e))
m_cond(x,z,u) = length(z) == 0 ? zeros(length(x)) : K(x,z) * ((K(z,z) + s*I) \ u)
K_cond(x,z) = length(z) == 0 ? K(x,x) : Symmetric(K(x,x) - K(x,z) * ((K(z,z) + s*I) \ K(z,x)))


Random.seed!(12)
r = rand(Normal(0,1/(2*pi*ls)),l)

phi(x) = sqrt(a/l) * vcat(sin.(2*pi*r.*x'),cos.(2*pi*r.*x'))
f(x,w) = phi(x)' * w

fn(x) = 0.375 * (x + sin(10*x - 5))

z = eltype(x)[]
u = eltype(x)[]
F = []
for t in 1:4
    w = rand(Normal(0,1),2*l,n)
    e = rand(MvNormal(zeros(length(z)), s*I),n)
    alpha = f_cond(x,z,u,w,e)
    push!(z, x[argmin(alpha)])
    push!(u, fn(z[end]))
    push!(F, alpha)
end



for t in 1:4
    @pgf Axis(
        {
            axis_lines = "none",
            height = "4.5cm",
            width = "6cm",
            xmin=-0.5, xmax=0.5, ymin=-1, ymax=1,
        },
        [raw"\node at (-0.5,-1) {};"],
        [raw"\node at (-0.5,1) {};"],
        [raw"\node at (0.5,1) {};"],
        [raw"\node at (0.5,-1) {};"],
        Plot(
            {
                no_markers,
                smooth,
                very_thick,
                color=colorant"#1f77b4",
                name_path = "upper",
            },
            Coordinates(x, m_cond(x,z[1:t-1],u[1:t-1]) + 1.96*sqrt.(diag(K_cond(x,z[1:t-1]))))
        ),
        Plot(
            {
                no_markers,
                smooth,
                very_thick,
                color=colorant"#1f77b4",
                name_path = "lower",
            },
            Coordinates(x, m_cond(x,z[1:t-1],u[1:t-1]) - 1.96*sqrt.(diag(K_cond(x,z[1:t-1]))))
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
                thick,
                dashed
            },
            Coordinates(x, fn.(x))
        ),
        Plot(
            {
                no_markers,
                smooth,
                ultra_thick,
                color=colorant"#1f77b4",
            },
            Coordinates(x, F[t][:,1])
        ),
        Plot(
            { 
                only_marks,
                thick,
                fill=weighted_color_mean(0.875,colorant"#ffffff",colorant"#1f77b4"),
            },
            Coordinates(z[1:t-1], u[1:t-1])
        ),
        VLine(
            { 
                dashed,
                opacity=0.5,
            },
            z[t]
        ),
        HLine(
            { 
                dashed,
                opacity=0.5,
            },
            minimum(F[t])
        )
    ) |> TikzPicture |> save_tex("gp-ts-$t.tex")
end
