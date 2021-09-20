include("plot.jl")
using Colors

x = -3.5:0.1:3.5
y = -1.75:0.05:1.75

weighted_color_mean(0.5,colorant"#ffffff",colorant"#1f77b4")
weighted_color_mean(0.5,colorant"#000000",colorant"#1f77b4")


@pgf Axis(
    {
        axis_lines = "none",
        height = "8.5cm",
        axis_equal,
        view = "{310}{22.5}",
    },
    Plot3(
        {
            no_markers,
            domain = "-1.75:1.75",
            samples = 2,
            samples_y = 0,
            very_thick,
            dashed,
            line_cap = "round",
        },
        "({-0.5},{x},{0})"
    ),
    ([[Plot3(
        {
            no_markers,
            domain = "-3.5:3.5",
            smooth,
            very_thick,
            color = colorant"#1f77b4",
            fill = colorant"#1f77b4",
            fill_opacity = 0.25,
        },
        Coordinates(vcat(x[1],x,x[end]), fill(y_cond, length(x)+2), vcat(0,exp.(.-(x .- y_cond).^2),0))
    ), Plot3(
        {
            no_markers,
            domain = "-3.5:3.5",
            very_thick,
            line_cap = "round",
        },
        Coordinates([x[1],x[end]], fill(y_cond,2), zeros(2)) 
    )] for y_cond in reverse(range(-1.75,1.75,length=5))]...)...,
    Plot3(
        {
            no_markers,
            domain = "-1.75:1.75",
            smooth,
            very_thick,
            color = colorant"#1f77b4",
            fill = colorant"#1f77b4",
            fill_opacity = 0.25,
        },
        Coordinates(fill(x[end],length(y)+2), vcat(y[1],y,y[end]), vcat(0, exp.(.-y.^2), 0))
    ),
    Plot3(
        {
            no_markers,
            domain = "-1.75:1.75",
            very_thick,
            line_cap = "round",
        },
        Coordinates(fill(x[end],2), [y[1],y[end]], zeros(2))
    )
) |> TikzPicture |> save_tex("bayes.tex")