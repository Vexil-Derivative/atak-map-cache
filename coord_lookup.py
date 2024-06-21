import json
import pandas as pd
from shapely.geometry import Polygon, Point, MultiPolygon
import us_state_abbrev as stateab

class Lookup:
    def __init__(self):
        data = json.load(open('us_states_geojson.json'))
        df = pd.DataFrame(data["features"])

        df['Location'] = df['properties'].apply(lambda x: x['NAME'])
        df['Type'] = df['geometry'].apply(lambda x: x['type'])
        df['Coordinates'] = df['geometry'].apply(lambda x: x['coordinates'])

        df_new = pd.DataFrame()
        lst_new = []

        self.FipsDF = pd.read_csv('fips2county.tsv', sep='\t', header='infer', dtype=str, encoding='latin-1')

        for idx, row in df.iterrows():

            if row['Type'] == 'MultiPolygon':
                list_of_polys = []
                df_row = row['Coordinates']
                for ll in df_row:
                    list_of_polys.append(Polygon(ll[0]))
                poly = MultiPolygon(list_of_polys)

            elif row['Type'] == 'Polygon':
                df_row = row['Coordinates']
                poly = Polygon(df_row[0])

            else:
                poly = None

            row['Polygon'] = poly
            lst_new.append(row)
        df_new = pd.DataFrame(lst_new)

        self.df_selection = df_new.drop(columns=['type', 'properties', 'geometry','Coordinates'] )
    
    def state(self, lat, lon, fp=''):

        if fp:
            state = self.FipsDF[self.FipsDF['StateFIPS'].astype(int) == fp]
            return state['StateAbbr'].iloc[0]
        else:
            try:
                point = Point(lon, lat)
            except ValueError:
                point = Point(float(lon.strip('[] ')), float(lat.strip('[] ')))
            state = self.df_selection.apply(lambda row: row['Location'] if row['Polygon'].contains(point) else None, axis=1).dropna()
        try:
            abbreviation = stateab.us_state_to_abbrev[state.iloc[0]]
        except IndexError:
            abbreviation = 'Unknown'
        return abbreviation

if __name__ == "__main__":
    lookup = Lookup()
    lookup.state(-81.47, 27.494)