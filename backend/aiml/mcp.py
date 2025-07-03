from mcp.server.fastmcp import FastMCP
import sympy as sp
import numpy as np
import requests
from typing import List, Optional
import io
import base64
import matplotlib.pyplot as plt
import plotly.express as px
import json
import urllib.parse

mcp = FastMCP("Math Tools MCP Server")

@mcp.tool(title="Symbolic Math (SymPy)", description="Evaluate symbolic math expressions using SymPy.")
def sympy_eval(expr: str) -> str:
    """
    Evaluate a symbolic math expression using SymPy.
    Args:
        expr: The symbolic expression to evaluate (as a string).
    Returns:
        The simplified result as a string, or an error message.
    """
    try:
        result = sp.sympify(expr)
        return str(sp.simplify(result))
    except Exception as e:
        return f"SymPy error: {e}"

@mcp.tool(title="Numeric Math (NumPy)", description="Evaluate numeric expressions using NumPy.")
def numpy_eval(expr: str) -> str:
    """
    Evaluate a numeric expression using NumPy.
    Args:
        expr: The numeric expression to evaluate (as a string, e.g., 'np.sin(np.pi/2)').
    Returns:
        The result as a string, or an error message.
    """
    try:
        return str(eval(expr, {"np": np, "__builtins__": {}}))
    except Exception as e:
        return f"NumPy error: {e}"

@mcp.tool(title="WolframAlpha", description="Query WolframAlpha for math answers.")
def wolfram_query(query: str, app_id: str) -> str:
    """
    Query WolframAlpha for a math answer.
    Args:
        query: The question or expression to send to WolframAlpha.
        app_id: Your WolframAlpha App ID.
    Returns:
        The result as a string, or an error message.
    """
    endpoint = "http://api.wolframalpha.com/v1/result"
    params = {"i": query, "appid": app_id}
    resp = requests.get(endpoint, params=params)
    if resp.status_code == 200:
        return resp.text
    return f"WolframAlpha error: {resp.text}"

@mcp.tool(title="MathJS", description="Evaluate math expressions using the MathJS API.")
def mathjs_eval(expr: str) -> str:
    """
    Evaluate a math expression using the MathJS API.
    Args:
        expr: The expression to evaluate.
    Returns:
        The result as a string, or an error message.
    """
    endpoint = "https://api.mathjs.org/v4/"
    resp = requests.post(endpoint, json={"expr": expr})
    if resp.status_code == 200:
        return resp.text
    return f"MathJS error: {resp.text}"

@mcp.tool(title="Matplotlib Plot", description="Create a plot using Matplotlib and return as a base64 PNG.")
def matplotlib_plot(x: List[float], y: List[float], plot_type: str = "line") -> str:
    """
    Create a plot using Matplotlib and return the image as a base64-encoded PNG.
    Args:
        x: List of x values.
        y: List of y values.
        plot_type: 'line' or 'scatter'.
    Returns:
        The plot as a base64-encoded PNG image string.
    """
    plt.figure()
    if plot_type == "scatter":
        plt.scatter(x, y)
    else:
        plt.plot(x, y)
    plt.xlabel("x")
    plt.ylabel("y")
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")
    return img_base64

@mcp.tool(title="Plotly Plot", description="Create a plot using Plotly and return as a base64 PNG.")
def plotly_plot(x: List[float], y: List[float], plot_type: str = "line") -> str:
    """
    Create a plot using Plotly and return the image as a base64-encoded PNG.
    Args:
        x: List of x values.
        y: List of y values.
        plot_type: 'line' or 'scatter'.
    Returns:
        The plot as a base64-encoded PNG image string.
    """
    if plot_type == "scatter":
        fig = px.scatter(x=x, y=y)
    else:
        fig = px.line(x=x, y=y)
    img_bytes = fig.to_image(format="png")
    img_base64 = base64.b64encode(img_bytes).decode("utf-8")
    return img_base64

@mcp.tool(title="Desmos Graph", description="Generate a Desmos graph URL for a given expression.")
def desmos_graph(expression: str) -> str:
    """
    Generate a Desmos graph URL for a given expression.
    Args:
        expression: The LaTeX expression to graph.
    Returns:
        A URL to the Desmos graph.
    """
    base_url = "https://www.desmos.com/calculator"
    state = {"expressions": {"list": [{"latex": expression}]}}
    url = f"{base_url}?state={urllib.parse.quote(json.dumps(state))}"
    return url

@mcp.tool(title="GeoGebra Graph", description="Generate a GeoGebra graph URL for a given expression.")
def geogebra_graph(expression: str) -> str:
    """
    Generate a GeoGebra graph URL for a given expression.
    Args:
        expression: The expression to graph (currently returns the base GeoGebra graphing URL).
    Returns:
        A URL to the GeoGebra graphing calculator.
    """
    # For more advanced use, see GeoGebra API docs
    base_url = "https://www.geogebra.org/graphing"
    return base_url

def run_server():
    """Run the MCP server. Call this from another file to start the server."""
    mcp.run()
