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
        list: A list of Plotly graph objects.
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

    # Create graphs
    graphs = []

    # Graph 1: Flight Hours by Month
    graphs.append(go.Figure(
        data=[go.Bar(x=list(flight_hours_by_month.keys()), y=list(flight_hours_by_month.values()))],
        layout=go.Layout(title="Flight Hours by Month", xaxis_title="Month", yaxis_title="Hours")
    ))

    # Graph 2: Flight Hours by Aircraft
    graphs.append(go.Figure(
        data=[go.Bar(x=list(flight_hours_by_aircraft.keys()), y=list(flight_hours_by_aircraft.values()))],
        layout=go.Layout(title="Flight Hours by Aircraft", xaxis_title="Aircraft", yaxis_title="Hours")
    ))

    # Graph 3: Flight Hours by Contract
    graphs.append(go.Figure(
        data=[go.Bar(x=list(flight_hours_by_contract.keys()), y=list(flight_hours_by_contract.values()))],
        layout=go.Layout(title="Flight Hours by Contract", xaxis_title="Contract", yaxis_title="Hours")
    ))

    # Graph 4: Flight Hours Comparison (Current Year vs Previous Year)
    graphs.append(go.Figure(
        data=[
            go.Bar(name="Current Year", x=list(flight_hours_comparison.keys()),
                   y=[data['current_year'] for data in flight_hours_comparison.values()]),
            go.Bar(name="Previous Year", x=list(flight_hours_comparison.keys()),
                   y=[data['previous_year'] for data in flight_hours_comparison.values()])
        ],
        layout=go.Layout(title="Flight Hours Comparison", xaxis_title="Month", yaxis_title="Hours", barmode="group")
    ))

    return graphs
