import dash
from dash import dcc, html, Input, Output, State
from poliastro.bodies import Earth
from poliastro.twobody import Orbit
from astropy import units as u
from poliastro.plotting.static import StaticOrbitPlotter
from astropy.time import Time


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

        html.Label("Resolution (m)"),
        dcc.Input(id='sensor-resolution', type='number', value=10),

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
        html.Div(id='power-budget-output', style={'fontSize': '18px'}),

        html.H2("Data Budget Analysis"),
        html.Div(id='data-budget-output', style={'fontSize': '18px'})
    ], style={'width': '70%', 'float': 'right', 'padding': '20px'})
])

# Helper Functions for Data Budget
def estimate_data_rate(sensor_type, resolution):
    # Sample data generation rates for different sensors
    if sensor_type == "MSI":
        return resolution * 0.1  # MB per orbit (simplified example)
    elif sensor_type == "HSI":
        return resolution * 0.5  # MB per orbit
    elif sensor_type == "SAR":
        return resolution * 1.0  # MB per orbit
    return 0

def calculate_onboard_storage(data_rate, downlink_time, mission_duration):
    # Simplified estimate of onboard storage
    data_per_day = data_rate * downlink_time
    return data_per_day * mission_duration  # MB or GB

# Callbacks
@app.callback(
    [Output('orbit-plot', 'figure'),
     Output('revisit-time-output', 'children'),
     Output('power-budget-output', 'children'),
     Output('data-budget-output', 'children')],
    Input('update-btn', 'n_clicks'),
    State('orbit-type', 'value'),
    State('altitude', 'value'),
    State('inclination', 'value'),
    State('sensor-type', 'value'),
    State('sensor-resolution', 'value'),
    State('solar-area', 'value'),
    State('solar-eff', 'value'),
    State('power-consumption', 'value')
)
def update_orbit(n_clicks, orbit_type, altitude, inclination, sensor_type, sensor_resolution, solar_area, solar_eff, power_consumption):
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

    # Plot orbit using matplotlib and convert to image
    fig, ax = plt.subplots(figsize=(6, 6))
    plotter = StaticOrbitPlotter(ax)
    plotter.set_attractor(Earth)
    plotter.plot(orbit, label="Selected Orbit", color='blue')
    ax.legend()
    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0}, showlegend=True, height=600)

    # Revisit Time Estimate
    earth_circumference_km = 40075
    swath = 100  # example fixed swath
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

    # Data Budget Analysis
    data_rate = estimate_data_rate(sensor_type, sensor_resolution)
    downlink_time = 12  # example: 12 hours of visibility per day
    mission_duration = 365  # 1-year mission
    required_storage = calculate_onboard_storage(data_rate, downlink_time, mission_duration)
    data_output = f"Estimated Onboard Storage Required: {required_storage:.1f} MB"

    return fig, revisit_output, power_output, data_output

if __name__ == '__main__':
    app.run(debug=True)
