include("plot.jl")
using Colors
using Distributions
using Random
using KernelFunctions
using LinearAlgebra: I, Symmetric, diag

z = range(0.05,0.35;length=10)
u = 0.5*sin.(10 .* (z .- 0.2))

x = 0:0.0125:1
a = 0.1
ls = 0.1
s = 0.000001^2
l = 128
n = 32

Random.seed!(1)
r = rand(Normal(0,1/(2*pi*ls)),l)
b = rand(Uniform(0,2*pi),l)
w = rand(Normal(0,1),2*l,n)
e = rand(MvNormal(zeros(length(z)), s*I),n)

phi(x) = sqrt(a/l) * vcat(sin.(2*pi*r.*x'),cos.(2*pi*r.*x'))
psi(x) = sqrt(2*a/l) * cos.(2*pi*r.*x' .+ b)

f(x) = phi(x)' * w
g(x) = psi(x)' * w[1:l,:]

f_cond = f(x) + phi(x)' * phi(z) * ((phi(z)' * phi(z) + s*I) \ (u .- f(z) .- e))
g_cond = g(x) + psi(x)' * psi(z) * ((psi(z)' * psi(z) + s*I) \ (u .- g(z) .- e))

m_f_cond = phi(x)' * phi(z) * ((phi(z)' * phi(z) + s*I) \ u)
K_f_cond = Symmetric(phi(x)' * phi(x) - phi(x)' * phi(z) * ((phi(z)' * phi(z) + s*I) \ (phi(z)' * phi(x))))

m_g_cond = psi(x)' * psi(z) * ((psi(z)' * psi(z) + s*I) \ u)
K_g_cond = Symmetric(psi(x)' * psi(x) - psi(x)' * psi(z) * ((psi(z)' * psi(z) + s*I) \ (psi(z)' * psi(x))))

k = a * with_lengthscale(SqExponentialKernel(), ls)
K_xx = kernelmatrix(k, x, x)
K_xz = kernelmatrix(k, x, z)
K_zz = kernelmatrix(k, z, z)

m_true = K_xz * ((K_zz + s*I) \ u)
K_true = Symmetric(K_xx - K_xz * ((K_zz + s*I) \ K_xz'))


for (s,m,K,name) in ((f_cond,m_f_cond,K_f_cond,"gp-vs"),(g_cond,m_g_cond,K_g_cond,"gp-vs-phase"))
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
        Plot(
            {
                no_markers,
                smooth,
                thick,
                dashed,
            },
            Coordinates(x, m_true + 1.96*sqrt.(diag(K_true)))
        ),
        Plot(
            {
                no_markers,
                smooth,
                thick,
                dashed,
            },
            Coordinates(x, m_true - 1.96*sqrt.(diag(K_true)))
        ),
        Plot(
            {
                no_markers,
                smooth,
                very_thick,
                dashed,
                
            },
            Coordinates(x, m_true)
        ),
        [Plot(
            {
                no_markers,
                smooth,
                thick,
                color=colorant"#1f77b4",
                opacity = 0.5
            },
            Coordinates(x, s[:,i])
        ) for i in 1:n]...,
        Plot(
            { 
                only_marks,
                thick,
                fill=weighted_color_mean(0.875,colorant"#ffffff",colorant"#1f77b4"),
            },
            Coordinates(z, u)
        ),
    ) |> TikzPicture |> save_tex("$name.tex")
end


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
    legend_entry("only marks, mark options={thick}, mark={*}, fill=$(color_to_pgf(weighted_color_mean(0.875,colorant"#ffffff",colorant"#1f77b4")))" => "Data"),
    legend_entry("fill opacity={0.25}, area legend, very thick, color=$(color_to_pgf(colorant"#1f77b4")), fill=$(color_to_pgf(colorant"#1f77b4"))" => "Approximate posteriors"),
    legend_entry("fill opacity={0}, area legend, thick, color={black}, dash pattern={on 0pt off 1.25pt on 3pt off 2.4375pt on 3pt off 3pt on 3pt off 3pt on 3pt off 2.4375pt on 3pt off 2.4375pt on 3pt off 3pt on 3pt off 3pt on 3pt off 3pt}" => "Exact posterior"),
    legend_entry("opacity={0.5}, thick, color=$(color_to_pgf(colorant"#1f77b4"))" => "Samples"),
) |> TikzPicture |> save_tex("gp-vs-lgnd.tex")