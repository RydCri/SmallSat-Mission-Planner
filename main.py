import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objs as go
from poliastro.bodies import Earth
from poliastro.twobody import Orbit
from astropy import units as u
from poliastro.plotting.static import StaticOrbitPlotter
from datetime import datetime

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

        html.Button("Update Orbit", id='update-btn')
    ], style={'width': '25%', 'float': 'left', 'padding': '20px'}),

    html.Div([
        html.H2("Orbit Visualization"),
        dcc.Loading(
            id="loading-plot",
            children=dcc.Graph(id='orbit-plot'),
            type="default"
        )
    ], style={'width': '70%', 'float': 'right', 'padding': '20px'})
])

# Callbacks
@app.callback(
    Output('orbit-plot', 'figure'),
    Input('update-btn', 'n_clicks'),
    State('orbit-type', 'value'),
    State('altitude', 'value'),
    State('inclination', 'value')
)
def update_orbit(n_clicks, orbit_type, altitude, inclination):
    # Defaults
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

    # Create orbit from altitude and inclination (circular orbit)
    a = Earth.R + alt
    ecc = 0 * u.one
    raan = 0 * u.deg
    argp = 0 * u.deg
    nu = 0 * u.deg

    orbit = Orbit.from_classical(Earth, a, ecc, inc, raan, argp, nu, epoch=datetime.utcnow())

    fig = go.Figure()
    plotter = StaticOrbitPlotter(fig)
    plotter.plot(orbit, label="Selected Orbit")

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        showlegend=True,
        height=600
    )
    return fig


if __name__ == '__main__':
    app.run(debug=True)
