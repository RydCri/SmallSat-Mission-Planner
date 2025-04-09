import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
from poliastro.bodies import Earth
from poliastro.twobody import Orbit
from astropy import units as u
from astropy.time import Time
from poliastro.plotting.static import StaticOrbitPlotter
import numpy as np

# Dash app configuration
app = dash.Dash(__name__)
app.title = "SmallSat Mission Planner"

# Layout
app.layout = html.Div([
    html.Div([
        html.H2("Mission Parameters"),

        html.Label("Orbit Type"),
        dcc.Dropdown(
            id='orbit-type',
            options=[
                {'label': 'LEO (500 km)', 'value': 'LEO'},
                {'label': 'SSO (Sun-Synchronous)', 'value': 'SSO'},
                {'label': 'Polar Orbit', 'value': 'POLAR'},
                {'label': 'Custom', 'value': 'CUSTOM'}
            ],
            value='LEO'
        ),

        html.Label("Altitude (km)"),
        dcc.Input(id='altitude', type='number', value=500),

        html.Label("Inclination (deg)"),
        dcc.Input(id='inclination', type='number', value=97.5),

        html.Hr(),

        html.H4("Sensor & Payload"),
        html.Label("Sensor Type"),
        dcc.Dropdown(
            id='sensor-type',
            options=[
                {'label': 'Multispectral Imager', 'value': 'MSI'},
                {'label': 'Hyperspectral Imager', 'value': 'HSI'},
                {'label': 'Synthetic Aperture Radar (SAR)', 'value': 'SAR'}
            ],
            value='MSI'
        ),

        html.Label("Swath Width (km)"),
        dcc.Input(id='swath-width', type='number', value=100),

        html.Hr(),

        html.H4("Power Budget"),
        html.Label("Solar Panel Area (m²)"),
        dcc.Input(id='solar-area', type='number', value=1.5),

        html.Label("Solar Cell Efficiency (%)"),
        dcc.Input(id='solar-eff', type='number', value=28),

        html.Label("Average Power Consumption (W)"),
        dcc.Input(id='power-consumption', type='number', value=50),

        html.Button("Update Orbit", id='update-btn')
    ], style={'width': '25%', 'float': 'left', 'padding': '20px'}),

    html.Div([
        html.H2("Orbit Visualization"),
        dcc.Loading(
            id="loading-plot",
            children=dcc.Graph(id='orbit-plot'),
            type="default"
        ),

        html.H2("Revisit Time Estimate"),
        html.Div(id='revisit-time-output', style={'fontSize': '18px'}),

        html.H2("Power Budget Analysis"),
        html.Div(id='power-budget-output', style={'fontSize': '18px'})
    ], style={'width': '70%', 'float': 'right', 'padding': '20px'})
])

# Callbacks
@app.callback(
    [Output('orbit-plot', 'figure'),
     Output('revisit-time-output', 'children'),
     Output('power-budget-output', 'children')],
    Input('update-btn', 'n_clicks'),
    State('orbit-type', 'value'),
    State('altitude', 'value'),
    State('inclination', 'value'),
    State('swath-width', 'value'),
    State('solar-area', 'value'),
    State('solar-eff', 'value'),
    State('power-consumption', 'value')
)

def estimate_data_rate(sensor_type, resolution, sensor_specs):
    if sensor_type == "MSI":
        # Data rate formula (example)
        return resolution * sensor_specs["number_of_bands"] * 10  # in MB per orbit
    elif sensor_type == "HSI":
        # Hyperspectral data is higher
        return resolution * sensor_specs["number_of_bands"] * 50  # in MB per orbit
    elif sensor_type == "SAR":
        # SAR data rate depends on the imaging mode
        return resolution * sensor_specs["imaging_mode_factor"] * 100  # in MB per orbit
    else:
        return 0

def downlink_opportunities(orbit, ground_station):
    # This function can compute ground station visibility during the orbit
    # Simplified model: Assuming a fixed downlink window for each pass
    pass

def update_orbit(n_clicks, orbit_type, altitude, inclination, swath_width, solar_area, solar_eff, power_consumption):
    if orbit_type == 'LEO':
        alt = 500 * u.km
        inc = 51.6 * u.deg
    elif orbit_type == 'SSO':
        alt = 600 * u.km
        inc = 97.5 * u.deg
    elif orbit_type == 'POLAR':
        alt = 700 * u.km
        inc = 90.0 * u.deg
    else:  # CUSTOM
        alt = (altitude or 500) * u.km
        inc = (inclination or 90) * u.deg

    # Orbit calculation
    a = Earth.R + alt
    ecc = 0 * u.one
    raan = 0 * u.deg
    argp = 0 * u.deg
    nu = 0 * u.deg

    orbit = Orbit.from_classical(Earth, a, ecc, inc, raan, argp, nu, epoch=Time.now())

    # Plot the orbit using Plotly
    fig = go.Figure()

    # Generate points for the orbit path (in 3D)
    num_points = 500
    times = np.linspace(0, 2 * np.pi, num_points)
    x_vals, y_vals, z_vals = [], [], []

    for t in times:
        pos = orbit.propagate(t)  # Propagate the orbit
        x_vals.append(pos.r[0].value)
        y_vals.append(pos.r[1].value)
        z_vals.append(pos.r[2].value)

    # Add orbit path to the plot
    fig.add_trace(go.Scatter3d(
        x=x_vals,
        y=y_vals,
        z=z_vals,
        mode='lines',
        line=dict(color='blue', width=4),
        name="Orbit Path"
    ))

    # Add Earth at the origin
    fig.add_trace(go.Scatter3d(
        x=[0],
        y=[0],
        z=[0],
        mode='markers',
        marker=dict(size=5, color='green'),
        name="Earth"
    ))

    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis_title='X (km)',
            yaxis_title='Y (km)',
            zaxis_title='Z (km)',
            aspectmode="cube"
        ),
        margin=dict(l=0, r=0, b=0, t=0),
        showlegend=True,
        height=600,
        title="Orbit Visualization"
    )

    # Revisit Time Estimate
    earth_circumference_km = 40075
    swath = swath_width or 100
    revisit_estimate_days = round(earth_circumference_km / (swath * 14), 1)
    revisit_output = f"Estimated Global Revisit Time: {revisit_estimate_days} days"

    # Power Budget Analysis
    solar_constant = 1361  # W/m²
    eclipse_fraction = 0.35  # rough average
    solar_efficiency = (solar_eff or 28) / 100
    area = solar_area or 1.5
    generated_power = solar_constant * area * solar_efficiency * (1 - eclipse_fraction)
    power_used = power_consumption or 50
    power_output = f"Average Power Generated: {generated_power:.1f} W — Consumption: {power_used} W"

    if generated_power >= power_used:
        power_output += " ✅ Power budget is sufficient."
    else:
        power_output += " ⚠️ Power budget is insufficient!"

    return fig, revisit_output, power_output

#TODO: Disable debug mode and set host and port for production
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=80)
