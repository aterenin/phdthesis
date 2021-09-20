import plotly.graph_objects as go
fig = go.Figure(go.Scattergeo())
fig.update_geos(visible=False, showland=True, landcolor="black", resolution=50, bgcolor="white")
fig.update_layout(autosize=True,height=350,margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="white")
fig.write_image("mercator.png",scale=32)