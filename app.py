from dash import Dash, html, dcc, Input, Output
import pandas as pd
import numpy as np
import plotly.express as px

DATA_FILE = "data/CO2.xlsx"
CURACAO_PATTERN = "^" + "".join(["Cur", "a"]) + ".*" + "ao$"

app = Dash(__name__)
app.title = "CO2 Dashboard"


def load_and_tidy_data(path):
    # Each workbook sheet has one column per year, so the dashboard first reshapes it to long format.
    totals = pd.read_excel(path, sheet_name="fossil_CO2_totals_by_country")
    per_capita = pd.read_excel(path, sheet_name="fossil_CO2_per_capita_by_countr")
    sectors = pd.read_excel(path, sheet_name="fossil_CO2_by_sector_and_countr")

    year_cols = [c for c in totals.columns[2:]]

    def tidy(df, value_name, id_vars):
        out = df.copy()

        # Normalize the country name when the workbook contains an encoded variant.
        out["Country"] = out["Country"].astype(str).str.replace(CURACAO_PATTERN, "Curacao", regex=True)

        # Remove non regions. I dont know if they should be included or not, but they break the density plot and are not very relevant for the dashboard
        #out = out[~out["Country"].isin(["International Shipping", "International Aviation"])].copy()

        out = out.melt(
            id_vars=id_vars,
            value_vars=year_cols,
            var_name="Year",
            value_name=value_name
        )

        out["Year"] = out["Year"].astype(int)
        return out

    totals_long = tidy(totals, "value", ["ISOcode", "Country"])
    totals_long["metric"] = "Total CO2 (Mt)"

    per_capita_long = tidy(per_capita, "value", ["ISOcode", "Country"])
    per_capita_long["metric"] = "CO2 per capita (t)"

    metrics_long = pd.concat([totals_long, per_capita_long], ignore_index=True)
    sectors_long = tidy(sectors, "value", ["Sector", "ISOcode", "Country"])

    # Keep selectors limited to countries that can be shown across all dashboard sections.
    countries = sorted(set(metrics_long["Country"]).intersection(set(sectors_long["Country"])))
    years = sorted(metrics_long["Year"].unique())

    return metrics_long, sectors_long, countries, years


metrics_long, sectors_long, countries, years = load_and_tidy_data(DATA_FILE)

default_countries = [c for c in ["Spain and Andorra", "France", "Germany"] if c in countries]
if not default_countries:
    default_countries = countries[:3]

default_country_single = "Spain and Andorra"
if default_country_single not in countries:
    default_country_single = countries[0]

#style for cards
card_style = {
    "backgroundColor": "#1e293b",
    "border": "1px solid #334155",
    "borderRadius": "12px",
    "padding": "16px",
    "textAlign": "center",
    "boxShadow": "0 1px 3px 0 rgba(0, 0, 0, 0.5), 0 1px 2px 0 rgba(0, 0, 0, 0.3)",
    "fontWeight": "600",
    "color": "#f8fafc",
    "fontSize": "15px"
}

#style for panels
panel_style = {
    "backgroundColor": "#1e293b",
    "border": "1px solid #334155",
    "borderRadius": "16px",
    "padding": "20px",
    "boxShadow": "0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3)",
    "color": "#f8fafc"
}

app.layout = html.Div([
    # HEADER ROW
    html.Div([
        html.Div([
            html.H1("ASTD Dashboard", style={"marginBottom": "4px"}),
            html.P("CO2 total/per capita, world map, sectors, ranking and density shift.", style={"marginTop": "0"}),
            
            html.Div([
                html.Div([
                    html.Label("Global Metric"),
                    dcc.Dropdown(
                        id="metric-dropdown",
                        options=[
                            {"label": "Total CO2 (Mt)", "value": "Total CO2 (Mt)"},
                            {"label": "CO2 per capita (t)", "value": "CO2 per capita (t)"}
                        ],
                        value="Total CO2 (Mt)",
                        clearable=False,
                        style={"color": "#0f172a", "backgroundColor": "#f8fafc"},
                        className="dark-dropdown"
                    )
                ], style={"minWidth": "220px", "flex": "1"}),

                html.Div([
                    html.Label("Global Year"),
                    dcc.Slider(
                        id="year-slider",
                        min=min(years),
                        max=max(years),
                        step=1,
                        value=max(years),
                        marks={int(y): {'label': str(y), 'style': {'color': '#94a3b8', 'fontWeight': '500'}} for y in years[::5]},
                        tooltip={"placement": "bottom"}
                    )
                ], style={"minWidth": "280px", "flex": "1.5"})
            ], style={"display": "flex", "gap": "20px", "marginTop": "15px", "maxWidth": "700px"})
        ], style={"flex": "1"}),
        
        # KPIs Block
        html.Div([
            html.Div([
                html.Label("Country for KPIs"),
                dcc.Dropdown(
                    id="kpi-country-selector",
                    options=[{"label": c, "value": c} for c in countries],
                    value=default_country_single,
                    clearable=False,
                    style={"color": "#0f172a", "backgroundColor": "#f8fafc"},
                    className="dark-dropdown"
                )
            ], style={"marginBottom": "10px", "maxWidth": "250px", "marginLeft": "auto"}),

            html.Div([
                html.Div(id="kpi-country", style=card_style),
                html.Div(id="kpi-world", style=card_style),
                html.Div(id="kpi-rank", style=card_style),
                html.Div(id="kpi-sector", style=card_style),
            ], style={
                "display": "grid",
                "gridTemplateColumns": "repeat(2, 1fr)",
                "gap": "10px"
            })
        ], style={"flex": "1", "minWidth": "420px"})
    ], style={"display": "flex", "gap": "20px", "flexWrap": "wrap", "marginBottom": "20px", "alignItems": "flex-start"}),

    # MIDDLE ROW (2 columns)
    html.Div([
        html.Div([
            html.Div([
                html.H3("TOTAL / PER CAPITA", style={"marginTop": "0"}),
                html.Label("Countries to compare"),
                dcc.Dropdown(
                    id="country-dropdown-multi",
                    options=[{"label": c, "value": c} for c in countries],
                    value=default_countries,
                    multi=True,
                    style={"marginBottom": "10px", "color": "#0f172a", "backgroundColor": "#f8fafc"},
                    className="dark-dropdown"
                ),
                dcc.Graph(id="line-chart", style={"height": "350px"})
            ], style=panel_style),

            html.Div([
                html.H3("RANKING", style={"marginTop": "0"}),
                html.Label("Top N", style={"display": "block", "marginBottom": "5px"}),
                dcc.Slider(
                    id="topn-slider",
                    min=5,
                    max=20,
                    step=1,
                    value=10,
                    marks={5: {'label': "5", 'style': {'color': '#94a3b8'}}, 10: {'label': "10", 'style': {'color': '#94a3b8'}}, 15: {'label': "15", 'style': {'color': '#94a3b8'}}, 20: {'label': "20", 'style': {'color': '#94a3b8'}}},
                    tooltip={"placement": "bottom"}
                ),
                dcc.Graph(id="ranking-chart", style={"height": "350px"})
            ], style=dict(panel_style, **{"flex": "1"}))
        ], style={"display": "flex", "flexDirection": "column", "gap": "12px", "flex": "1.45"}),

        html.Div([
            html.Div([
                html.H3("MAP", style={"marginTop": "0"}),
                dcc.Graph(id="map-chart", style={"height": "430px"}),
                html.Div([
                    html.Label("Map Year"),
                    dcc.Slider(
                        id="map-year-slider",
                        min=min(years),
                        max=max(years),
                        step=1,
                        value=max(years),
                        marks=None,
                        tooltip={"placement": "bottom"}
                    )
                ], style={"marginTop": "10px"})
            ], style=panel_style),

            html.Div([
                html.Div([
                    html.H3("GIF", style={"margin": "0"}),
                    html.Button("Refresh", id="refresh-gif-btn", style={
                        "backgroundColor": "#3b82f6",
                        "color": "white",
                        "border": "none",
                        "borderRadius": "6px",
                        "padding": "6px 12px",
                        "cursor": "pointer",
                        "fontWeight": "600",
                        "boxShadow": "0 1px 2px rgba(0,0,0,0.2)"
                    })
                ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px"}),
                dcc.Dropdown(
                    id="gif-metric-dropdown",
                    options=[
                        {"label": "CO2 per capita (t)", "value": "per_capita"},
                        {"label": "Total CO2 (Mt)", "value": "total"}
                    ],
                    value="per_capita",
                    clearable=False,
                    style={"marginBottom": "10px", "color": "#0f172a", "backgroundColor": "#f8fafc"},
                    className="dark-dropdown"
                ),
                html.Img(
                    id="gif-image",
                    src="/assets/density_per_capita.gif",
                    style={
                        "width": "100%",
                        "height": "330px",
                        "objectFit": "contain",
                        "border": "1px solid #334155",
                        "borderRadius": "8px",
                        "backgroundColor": "#0f172a"
                    }
                ),
            ], style=panel_style)
        ], style={"display": "flex", "flexDirection": "column", "gap": "12px", "flex": "1"})
    ], style={"display": "flex", "gap": "12px", "marginBottom": "12px"}),
    
    # BOTTOM ROW (Full width)
    html.Div([
        html.Div([
            html.Div([
                html.H3("SECTORS", style={"margin": "0"}),
                html.Div([
                    html.Label("Country for Sectors", style={"marginRight": "10px", "fontWeight": "500", "alignSelf": "center"}),
                    dcc.Dropdown(
                        id="sectors-country-selector",
                        options=[{"label": c, "value": c} for c in countries],
                        value=default_country_single,
                        clearable=False,
                        style={"minWidth": "250px", "color": "#0f172a", "backgroundColor": "#f8fafc"},
                        className="dark-dropdown"
                    )
                ], style={"display": "flex", "alignItems": "center"})
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px"}),
            dcc.Graph(id="sector-chart", style={"height": "320px"})
        ], style=dict(panel_style, **{"flex": "1"})),

        html.Div([
            html.Div([
                html.H3("COMPOSITION", style={"margin": "0"}),
                html.Div([
                    html.Label("Year", style={"marginRight": "15px", "fontWeight": "500"}),
                    html.Div(
                        dcc.Slider(
                            id="composition-year-slider",
                            min=min(years),
                            max=max(years),
                            step=1,
                            value=max(years),
                            marks=None,
                            tooltip={"placement": "bottom"}
                        ),
                        style={"flex": "1", "minWidth": "200px"}
                    )
                ], style={"display": "flex", "alignItems": "center", "flex": "0.7", "justifyContent": "flex-end"})
            ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center", "marginBottom": "10px", "height": "36px"}),
            dcc.Graph(id="sector-pie-chart", style={"height": "320px"})
        ], style=dict(panel_style, **{"flex": "1"}))
    ], style={"display": "flex", "gap": "16px"})
], style={
    "width": "100%",
    "minHeight": "100vh",
    "boxSizing": "border-box",
    "padding": "24px", 
    "backgroundColor": "#0f172a",
    "fontFamily": "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    "color": "#f8fafc"
})


@app.callback(
    Output("map-chart", "figure"),
    Input("metric-dropdown", "value"),
    Input("map-year-slider", "value")
)
def update_map(metric, year):
    # The map and ranking share the same global metric selector.
    df = metrics_long[
        (metrics_long["metric"] == metric) &
        (metrics_long["Year"] == year)
    ].dropna(subset=["value"])

    fig = px.choropleth(
        df,
        locations="ISOcode",
        locationmode="ISO-3",
        color="value",
        hover_name="Country",
        color_continuous_scale="Teal",
        title=f"{metric} in {year}",
        labels={"value": metric},
        template="plotly_dark"
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=60, b=20))
    fig.update_geos(
        projection_type="equal earth",
        showcountries=True,
        countrycolor="#334155",
        showcoastlines=True,
        coastlinecolor="#475569",
        showland=True,
        landcolor="#1e293b",
        showocean=True,
        oceancolor="#0f172a"
    )
    return fig


@app.callback(
    Output("line-chart", "figure"),
    Input("metric-dropdown", "value"),
    Input("country-dropdown-multi", "value")
)
def update_line(metric, selected_countries):
    if not selected_countries:
        selected_countries = [default_country_single]

    df = metrics_long[
        (metrics_long["metric"] == metric) &
        (metrics_long["Country"].isin(selected_countries))
    ].dropna(subset=["value"])

    fig = px.line(
        df,
        x="Year",
        y="value",
        color="Country",
        markers=True,
        title=f"Time trend of {metric}",
        labels={"value": metric, "Year": "Year"},
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Prism
    )
    fig.update_traces(line=dict(width=3), marker=dict(size=8))
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=60, b=20))
    return fig


@app.callback(
    Output("sector-chart", "figure"),
    Input("sectors-country-selector", "value")
)
def update_sector_chart(country):
    df = sectors_long[sectors_long["Country"] == country].dropna(subset=["value"])

    fig = px.area(
        df,
        x="Year",
        y="value",
        color="Sector",
        title=f"Sectoral CO2 composition - {country}",
        labels={"value": "CO2 (Mt)", "Year": "Year"},
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=60, b=20))
    return fig


@app.callback(
    Output("sector-pie-chart", "figure"),
    Input("sectors-country-selector", "value"),
    Input("composition-year-slider", "value")
)
def update_sector_pie_chart(country, year):
    # Aggregate by sector for the selected country/year to get a compact composition snapshot.
    df = sectors_long[
        (sectors_long["Country"] == country) &
        (sectors_long["Year"] == year)
    ].dropna(subset=["value"])

    fig = px.pie(
        df,
        names="Sector",
        values="value",
        title=f"Sector mix of CO2 - {country} ({year})",
        hole=0.45,
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=60, b=20))
    return fig


@app.callback(
    Output("ranking-chart", "figure"),
    Input("metric-dropdown", "value"),
    Input("year-slider", "value"),
    Input("topn-slider", "value")
)
def update_ranking(metric, year, topn):
    df_metric = metrics_long[metrics_long["metric"] == metric].dropna(subset=["value"])
    
    # Calculate standard deviation for all top countries across all years
    std_devs = df_metric.groupby("Country")["value"].std().fillna(0)
    
    # Filter for the specific year and get top N
    df_year = df_metric[df_metric["Year"] == year]
    df_year = df_year.nlargest(topn, "value").sort_values("value")
    
    # Map std dev back to the dataframe
    df_year["std_dev"] = df_year["Country"].map(std_devs)

    fig = px.bar(
        df_year,
        x="value",
        y="Country",
        error_x="std_dev",
        orientation="h",
        title=f"Top {topn} countries - {metric} ({year})",
        labels={"value": metric, "Country": "Country"},
        template="plotly_dark",
        color_discrete_sequence=["#60a5fa"]
    )
    fig.update_traces(marker_line_width=0, opacity=0.9)
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=20, r=20, t=60, b=20))
    return fig


@app.callback(
    Output("kpi-country", "children"),
    Output("kpi-world", "children"),
    Output("kpi-rank", "children"),
    Output("kpi-sector", "children"),
    Input("metric-dropdown", "value"),
    Input("year-slider", "value"),
    Input("kpi-country-selector", "value")
)
def update_kpis(metric, year, country):
    metric_year = metrics_long[
        (metrics_long["metric"] == metric) &
        (metrics_long["Year"] == year)
    ].dropna(subset=["value"])

    country_value = metric_year.loc[metric_year["Country"] == country, "value"]
    country_value = country_value.iloc[0] if not country_value.empty else np.nan

    if metric == "Total CO2 (Mt)":
        world_value = metric_year["value"].sum()
        world_title = "World total"
        world_suffix = "Mt"
        suffix = "Mt"
    else:
        world_value = metric_year["value"].mean()
        world_title = "World average"
        world_suffix = "t"
        suffix = "t"

    # Ranking is recomputed for the currently selected metric and year.
    ranking = metric_year.sort_values("value", ascending=False).reset_index(drop=True)
    country_rank_list = ranking.index[ranking["Country"] == country].tolist()
    country_rank = country_rank_list[0] + 1 if country_rank_list else "N/A"

    sector_year = sectors_long[
        (sectors_long["Country"] == country) &
        (sectors_long["Year"] == year)
    ].dropna(subset=["value"])

    if not sector_year.empty:
        top_sector_row = sector_year.sort_values("value", ascending=False).iloc[0]
        top_sector = f'{top_sector_row["Sector"]} ({top_sector_row["value"]:.2f} Mt)'
    else:
        top_sector = "No data"

    if pd.isna(country_value):
        country_text = f"{country}: no data"
    else:
        country_text = f"{country}: {country_value:.2f} {suffix}"

    world_text = f"{world_title}: {world_value:.2f} {world_suffix}"
    rank_text = f"Global rank: #{country_rank}"
    sector_text = f"Top sector: {top_sector}"

    return country_text, world_text, rank_text, sector_text


@app.callback(
    Output("gif-image", "src"),
    Input("gif-metric-dropdown", "value"),
    Input("refresh-gif-btn", "n_clicks"),
    prevent_initial_call=True
)
def refresh_gif(metric, n):
    # GIFs are pre-generated assets; the query string only busts the browser cache.
    gif_paths = {
        "per_capita": "/assets/density_per_capita.gif",
        "total": "/assets/density_total.gif",
    }
    version = n or 0
    return f"{gif_paths.get(metric, gif_paths['per_capita'])}?v={version}"


if __name__ == "__main__":
    app.run(debug=True)
