from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Weather")


@mcp.tool()
async def get_current_temperature(city: str) -> float:
    # Dummy implementation, replace with actual API call to get temperature
    dummy_temperatures = {
        "New York": 22.0,
        "Los Angeles": 25.5,
        "Chicago": 18.3,
        "Houston": 28.4,
        "Miami": 30.0,
    }
    return dummy_temperatures.get(city, 20.0)  # Default to 20.0 if city not found


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
