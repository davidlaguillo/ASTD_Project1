import os

import imageio.v2 as imageio
import numpy as np
import pandas as pd
import plotly.graph_objects as go


DATA_FILE = "data/CO2.xlsx"
FPS = 6
CURACAO_PATTERN = "^" + "".join(["Cur", "a"]) + ".*" + "ao$"

CONFIGS = [
    # One configuration per dashboard GIF.
    {
        "sheet_name": "fossil_CO2_per_capita_by_countr",
        "output_dir": "output/density_per_capita",
        "gif_paths": ["output/density_per_capita.gif", "assets/density_per_capita.gif"],
        "title": "CO2 per capita density",
        "xaxis_title": "CO2 per capita (t)",
    },
    {
        "sheet_name": "fossil_CO2_totals_by_country",
        "output_dir": "output/density_total",
        "gif_paths": ["output/density_total.gif", "assets/density_total.gif"],
        "title": "Total CO2 density",
        "xaxis_title": "Total CO2 (Mt)",
    },
]


def clean_values(df, year):
    # Density curves exclude transport pseudo-regions so they only describe countries.
    values = (
        df[["Country", year]]
        .rename(columns={year: "value"})
    )
    values["Country"] = values["Country"].astype(str).str.replace(CURACAO_PATTERN, "Curacao", regex=True)
    values = values[~values["Country"].isin(["International Shipping", "International Aviation"])]
    return values["value"].dropna().to_numpy()


def build_density_gif(config):
    df = pd.read_excel(DATA_FILE, sheet_name=config["sheet_name"])
    year_cols = sorted(c for c in df.columns[2:])
    base_year = min(year_cols)
    base_mu = clean_values(df, base_year).mean()

    os.makedirs(config["output_dir"], exist_ok=True)
    for gif_path in config["gif_paths"]:
        os.makedirs(os.path.dirname(gif_path), exist_ok=True)

    stats = {}
    span_global = 0.0
    for year in year_cols:
        values = clean_values(df, year)
        mu = values.mean()
        sigma = values.std(ddof=1)
        if sigma == 0:
            raise ValueError(
                f"The standard deviation is 0 in {year}; a normal curve cannot be drawn."
            )

        span = max(np.abs(values - base_mu).max(), 3 * sigma)
        span_global = max(span_global, span)
        stats[year] = {"mu": mu, "sigma": sigma}

    # All frames use the same x-axis range so movement over time is visually comparable.
    x = np.linspace(base_mu - span_global, base_mu + span_global, 400)

    frames = []
    for year in year_cols:
        mu = stats[year]["mu"]
        sigma = stats[year]["sigma"]
        pdf = (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x - mu) / sigma) ** 2)

        fig = go.Figure()
        fig.add_scatter(
            x=x,
            y=pdf,
            mode="lines",
            name="Normal curve (sample mean and standard deviation)",
            line=dict(width=3),
        )
        fig.add_vline(
            x=base_mu,
            line_width=2,
            line_dash="dash",
            annotation_text=f"Base mean ({base_year}) = {base_mu:.2f}",
            annotation_position="top right",
        )
        fig.add_vline(
            x=mu,
            line_width=2,
            line_dash="dot",
            line_color="gray",
            annotation_text=f"Mean {year} = {mu:.2f}",
            annotation_position="top left",
        )
        fig.update_layout(
            title=f"{config['title']} ({year}), centered on {base_year}",
            xaxis=dict(
                title=config["xaxis_title"],
                range=[base_mu - span_global, base_mu + span_global],
            ),
            yaxis_title="Density",
            template="plotly_white",
        )

        png_path = os.path.join(config["output_dir"], f"density_{year}.png")
        # Reuse existing frames when only the final GIF needs to be rebuilt.
        if not os.path.exists(png_path):
            fig.write_image(png_path, scale=2)
        frames.append(imageio.imread(png_path))

    for gif_path in config["gif_paths"]:
        imageio.mimsave(gif_path, frames, fps=FPS)
        print(f"GIF saved to: {gif_path}")


if __name__ == "__main__":
    for config in CONFIGS:
        build_density_gif(config)
