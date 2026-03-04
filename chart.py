import requests
import pandas as pd
import plotly.graph_objects as go

# List of gage IDs you want to generate hydrographs for
gage_ids = ["BRKM2", "EDFM2", "PORM2", "MILW2", "HFEW2", "SHEW2", "HNKM2", "PAWW2"]  

headers = {"User-Agent": "myapp (janicedevlin@gmail.com)"}

def df_from(entries):
    df = pd.DataFrame(entries)
    if not df.empty and 'validTime' in df.columns and 'primary' in df.columns:
        df['validTime'] = pd.to_datetime(df['validTime'])
        df['primary'] = pd.to_numeric(df['primary'], errors='coerce')
        # Filter out bad or unrealistic values
        df = df[df['primary'].notna() & (df['primary'] > -100) & (df['primary'] < 100)]
        return df
    return pd.DataFrame()

# Loop through each gage ID
for gage_id in gage_ids:
    url = f"https://api.water.noaa.gov/nwps/v1/gauges/{gage_id}/stageflow"
    print(f"Fetching data for gage {gage_id}...")

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching data for {gage_id}: {e}")
        continue

    df_obs = df_from(data.get("observed", {}).get("data", []))
    df_fcst = df_from(data.get("forecast", {}).get("data", []))

    # Keep only last 7 days of observations
    if not df_obs.empty:
        one_week_ago = df_obs['validTime'].max() - pd.Timedelta(days=6)
        df_obs = df_obs[df_obs['validTime'] >= one_week_ago]

    # Build the hydrograph
    fig = go.Figure()

    if not df_obs.empty:
        fig.add_trace(go.Scatter(
            x=df_obs["validTime"],
            y=df_obs["primary"],
            mode='lines+markers',
            name='Observed'
        ))

    if not df_fcst.empty:
        fig.add_trace(go.Scatter(
            x=df_fcst["validTime"],
            y=df_fcst["primary"],
            mode='lines+markers',
            name='Forecast'
        ))

    # Set layout
    original_height = 600

    fig.update_layout(
        title=f"NOAA Forecast level at {gage_id}",
        yaxis_title="Stage (feet)",
        template="plotly_white",
        height=int(original_height * 0.6),
        # margin=dict(l=40, r=20, t=60, b=40)
        margin=dict(l=40, r=20, t=80, b=40),  # increased top margin for legend
        legend=dict(
            orientation="h",   # horizontal legend
            yanchor="bottom",
            y=1.02,            # just above the chart
            xanchor="center",
            x=0.5
        )
    )

    # Write to HTML file
    output_filename = f"live_hydrograph_{gage_id}.html"
    fig.write_html(output_filename, include_plotlyjs='cdn', full_html=True)
    print(f"✅ Saved hydrograph: {output_filename}")

print("All hydrographs generated successfully.")
