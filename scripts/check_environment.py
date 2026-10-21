"""UrbanTwin Environment Verification Script.

Checks for the presence and version of all essential geospatial,
network, scientific, and database libraries, providing actionable
installation instructions if any dependencies are missing.
"""

import importlib
import sys
from typing import Dict, List, Optional, Tuple

# Core mandatory packages specified in requirements
CHECK_PACKAGES = [
    # Core Geospatial
    ("h3", "H3", "pip install h3"),
    ("geopandas", "GeoPandas", "pip install geopandas"),
    ("shapely", "Shapely", "pip install shapely"),
    ("pyproj", "PyProj", "pip install pyproj"),
    ("fiona", "Fiona", "pip install fiona"),
    ("rasterio", "Rasterio", "pip install rasterio"),
    # Mapping & Networks
    ("osmnx", "OSMnx", "pip install osmnx"),
    ("networkx", "NetworkX", "pip install networkx"),
    ("folium", "Folium", "pip install folium"),
    ("contextily", "Contextily", "pip install contextily"),
    # Scientific & Data Processing
    ("pandas", "Pandas", "pip install pandas"),
    ("numpy", "NumPy", "pip install numpy"),
    ("scipy", "SciPy", "pip install scipy"),
    ("matplotlib", "Matplotlib", "pip install matplotlib"),
    ("plotly", "Plotly", "pip install plotly"),
    # Database
    ("sqlalchemy", "SQLAlchemy", "pip install sqlalchemy"),
    ("psycopg2", "Psycopg2", "pip install psycopg2-binary"),
    ("alembic", "Alembic", "pip install alembic"),
    # Utilities
    ("dotenv", "Python-Dotenv", "pip install python-dotenv"),
    ("requests", "Requests", "pip install requests"),
    ("httpx", "HTTPX", "pip install httpx"),
]


def check_single_package(module_name: str, display_name: str, install_cmd: str) -> Tuple[bool, str, Optional[str]]:
    """Attempt to import a package and retrieve its version string."""
    try:
        mod = importlib.import_module(module_name)
        version = getattr(mod, "__version__", "installed")
        return True, f"OK ({version})", None
    except ImportError as err:
        return False, f"FAILED ({err.__class__.__name__})", install_cmd
    except Exception as err:
        return False, f"ERROR ({err})", install_cmd


def main() -> None:
    """Run verification checks and print formatted summary."""
    print("=" * 68)
    print(" UrbanTwin Geospatial Python Environment Verification")
    print(f" Python Executable: {sys.executable}")
    print(f" Python Version:    {sys.version.split()[0]}")
    print("=" * 68)

    missing_instructions: List[str] = []
    success_count = 0

    for module_name, display_name, install_cmd in CHECK_PACKAGES:
        success, status_str, suggestion = check_single_package(module_name, display_name, install_cmd)
        dots = "." * (24 - len(display_name))

        if success:
            success_count += 1
            print(f"  {display_name} {dots} {status_str}")
        else:
            print(f"  {display_name} {dots} {status_str}")
            if suggestion:
                missing_instructions.append(f"    - {display_name}: {suggestion}")

    print("-" * 68)

    if missing_instructions:
        print(f"\n[!] Verification FAILED: {len(missing_instructions)} package(s) missing or broken.")
        print("\nInstallation Suggestions:")
        for instruction in missing_instructions:
            print(instruction)
        print("\nQuick Fix:")
        print("  pip install -r requirements.txt\n")
        sys.exit(1)
    else:
        print(f"\n[SUCCESS] All {success_count} essential packages verified successfully!")
        print("          UrbanTwin geospatial research platform is ready to run.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
