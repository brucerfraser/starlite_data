import anvil.server
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import plotly.graph_objects as go
from .local_data import package_flights, MONTH_NAMES

# This is a module.
# You can define variables and functions here, and use them from any form. For example, in a top-level form:
#
#    from .. import Module1
#
#    Module1.say_hello()
#


def create_graphs(package):
    """
    Creates four graphs based on the filtered FLIGHTS data.

    Args:
        package (dict): A dictionary containing filter criteria for FLIGHTS.

    Returns:
        list: A list of (traces, layout) tuples for Plotly graphs.
    """
    # Filter FLIGHTS data using the package
    flights = package_flights(package)

    # Prepare data for graphs
    months = MONTH_NAMES
    flight_hours_by_month = {month: 0 for month in months}
    flight_hours_by_aircraft = {}
    flight_hours_by_contract = {}
    flight_hours_comparison = {month: {'current_year': 0, 'previous_year': 0} for month in months}

    for flight in flights:
        month_name = MONTH_NAMES[flight['FltDate'].month - 1]
        flight_hours_by_month[month_name] += flight['Block Time'] or 0

        aircraft = flight['Rego']
        flight_hours_by_aircraft[aircraft] = flight_hours_by_aircraft.get(aircraft, 0) + (flight['Block Time'] or 0)

        contract = flight['CFF_Client']
        flight_hours_by_contract[contract] = flight_hours_by_contract.get(contract, 0) + (flight['Block Time'] or 0)

        year = flight['FltDate'].year
        if year == int(package['years'][0]):  # Current year
            flight_hours_comparison[month_name]['current_year'] += flight['Block Time'] or 0
        elif year == int(package['years'][0]) - 1:  # Previous year
            flight_hours_comparison[month_name]['previous_year'] += flight['Block Time'] or 0

    for k in flight_hours_by_month:
        print(k,flight_hours_by_month[k])

    # Create graphs
    graphs = []

    # Graph 1: Flight Hours by Month (Waterfall Chart)
    cumulative_hours = []
    total = 0
    for month in months:
        total += flight_hours_by_month[month]
        cumulative_hours.append(flight_hours_by_month[month])
    print(cumulative_hours)
    traces = [{
        "type": "waterfall",
        "x": months,
        "y": cumulative_hours,
        "connector": {"line": {"color": "rgb(63, 63, 63)"}}
    }]
    layout = {
        "title": "Flight Hours by Month (Cumulative)",
        "xaxis": {"title": "Month"},
        "yaxis": {"title": "Cumulative Hours"}
    }
    graphs.append((traces, layout))

    # Graph 2: Flight Hours by Aircraft (Sorted Bar Chart)
    sorted_aircraft = sorted(flight_hours_by_aircraft.items(), key=lambda x: x[1], reverse=True)
    traces = [{
        "type": "bar",
        "x": [item[0] for item in sorted_aircraft],
        "y": [item[1] for item in sorted_aircraft]
    }]
    layout = {
        "title": "Flight Hours by Aircraft (Sorted)",
        "xaxis": {"title": "Aircraft"},
        "yaxis": {"title": "Hours"}
    }
    graphs.append((traces, layout))

    # Graph 3: Flight Hours by Contract (Sorted Bar Chart)
    sorted_contracts = sorted(flight_hours_by_contract.items(), key=lambda x: x[1], reverse=True)
    traces = [{
        "type": "bar",
        "x": [item[0] for item in sorted_contracts],
        "y": [item[1] for item in sorted_contracts]
    }]
    layout = {
        "title": "Flight Hours by Contract (Sorted)",
        "xaxis": {"title": "Contract"},
        "yaxis": {"title": "Hours"}
    }
    graphs.append((traces, layout))

    # Graph 4: Flight Hours Comparison (Current Year vs Previous Year)
    traces = [
        {
            "type": "bar",
            "name": "Current Year",
            "x": list(flight_hours_comparison.keys()),
            "y": [data['current_year'] for data in flight_hours_comparison.values()]
        },
        {
            "type": "bar",
            "name": "Previous Year",
            "x": list(flight_hours_comparison.keys()),
            "y": [data['previous_year'] for data in flight_hours_comparison.values()]
        }
    ]
    layout = {
        "title": "Flight Hours Comparison",
        "xaxis": {"title": "Month"},
        "yaxis": {"title": "Hours"},
        "barmode": "group"
    }
    graphs.append((traces, layout))

    return graphs
