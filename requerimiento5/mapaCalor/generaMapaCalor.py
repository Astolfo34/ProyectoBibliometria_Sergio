import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
import os
import pycountry

# Define the relative path to the CSV file using os.path.join
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "requerimiento5", "data", "resolved_affiliations.csv")

# Load the data and strip whitespace from column names
data = pd.read_csv(file_path)
data.columns = data.columns.str.strip()

# Count occurrences of each country
country_counts = data['pais'].value_counts().reset_index()
country_counts.columns = ['country', 'count']

# Debug: Print unique country codes in resolved_affiliations.csv
print("Unique country codes in resolved_affiliations.csv:", country_counts['country'].unique())

# Clean country codes in resolved_affiliations.csv
country_counts['country'] = country_counts['country'].str.strip()

# Convert Alpha-2 country codes to Alpha-3
country_counts['country'] = country_counts['country'].apply(
    lambda x: pycountry.countries.get(alpha_2=x).alpha_3 if pycountry.countries.get(alpha_2=x) else x
)

# Load a world map from the downloaded Natural Earth data
ruta_relativa= "requerimiento5/data/data_mapasCalor/ne_110m_admin_0_countries.shp"
natural_earth_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ruta_relativa)
world = gpd.read_file(natural_earth_path)

# Debug: Print available columns in the world DataFrame
print("Available columns in world DataFrame:", world.columns)

# Update the merge to use the correct column for country codes
if 'iso_a2' in world.columns:
    merge_column = 'iso_a2'
elif 'ADM0_A3' in world.columns:
    merge_column = 'ADM0_A3'
else:
    raise KeyError("No suitable column found in the world DataFrame for merging with country codes.")

# Debug: Print unique country codes in the world DataFrame
print(f"Unique country codes in the world DataFrame ({merge_column}):", world[merge_column].unique())

# Merge the data with the world map
world = world.merge(country_counts, how='left', left_on=merge_column, right_on='country')

# Replace NaN values with 0 for countries with no data
world['count'] = world['count'].fillna(0)

# Plot the heatmap
fig, ax = plt.subplots(1, 1, figsize=(15, 10))
divider = make_axes_locatable(ax)
cax = divider.append_axes("right", size="5%", pad=0.1)
world.plot(column='count', ax=ax, legend=True, cax=cax,
            legend_kwds={'label': "Number of Affiliations"},
            cmap='OrRd', edgecolor='black')

ax.set_title('Geographic Heatmap of Affiliations', fontsize=16)
ax.set_axis_off()

# Show the plot
plt.show()

# Save the heatmap as an image
output_path = os.path.join(os.path.dirname(file_path),'data_mapasCalor', 'heatmap_affiliations.png')
fig.savefig(output_path, dpi=300, bbox_inches='tight')
print(f"Heatmap saved as: {output_path}")