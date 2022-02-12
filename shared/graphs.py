import json
from datetime import datetime
from typing import IO

from pandas import DataFrame
from plotly.graph_objects import Scatter
from plotly.subplots import make_subplots


def create_graph(data: list[dict]):
    dt = DataFrame(data)
    figure = make_subplots(rows=3, cols=1)

    figure.add_trace(
        Scatter(
            x=[datetime.fromisoformat(x[:-1]) for x in dt['lastUpdatedAtSource']], y=dt['dailyPositiveTests'],
            name='infections',
            mode="lines+markers+text", text=[None] + [t - y for t, y in zip(dt['dailyPositiveTests'][1:], dt['dailyPositiveTests'][:-1])],
            textposition="top left", line={'color': '#50cc71', 'shape': 'spline'}
        ), row=1, col=1
    )
    figure.add_trace(
        Scatter(x=[datetime.fromisoformat(x[:-1]) for x in dt['lastUpdatedAtSource']], y=dt['dailyRecovered'],
                mode='lines', name='recovered', line={'dash': 'dash', 'color': '#8fb9cf', 'shape': 'spline'}),
        row=1, col=1
    )
    figure.add_trace(
        Scatter(x=[datetime.fromisoformat(x[:-1]) for x in dt['lastUpdatedAtSource']], y=dt['dailyDeceased'],
                mode='lines+markers', name='deaths', line={'shape': 'spline', 'color': '#4f423f'}),
        row=2, col=1
    )
    figure.add_trace(
        Scatter(
            x=[datetime.fromisoformat(x[:-1]) for x in dt['lastUpdatedAtSource']],
            y=[i - r - d for i, r, d in zip(dt['dailyPositiveTests'], dt['dailyRecovered'], dt['dailyDeceased'])],
            mode='lines+markers', name='result', line={'shape': 'spline', 'color': '#b53f92'}
        ),
        row=3, col=1
    )

    figure.update_layout(title={'text': f'COVID-19 tracker (last {len(data)} days)'}, legend={'orientation': 'h'}, width=1200,
                         height=800)

    return figure
