import numpy as np 
import pandas as pd
import matplotlib.pyplot as plt
import sys
import json
import csv
import gmplot as gmp
from uszipcode import SearchEngine

def import_data(input_file, zipcode_file, key_column, state, columns: dict, merge: list):
    #read file
    df_out = pd.read_csv(input_file, usecols=list(columns.values()) + [key_column, "State"])
    #select only michigan data
    df_out = df_out[df_out["State"] == "MI"]
    #remove state column, you don't need it
    df_out = df_out.drop("State", axis=1)
    #rename columns to be consistent regardless of unit
    rename_cols = {columns[k]:k for k in columns.keys()}
    df_out = df_out.rename(columns=rename_cols)
    #delete rows with no result value
    df_out.replace('', np.nan, inplace=True)
    df_out.dropna(subset=['value'], inplace=True)
    #df_out = df_out[not pd.isna(df_out['value'])]
    reader = csv.reader(open(zipcode_file))
    d = {}
    for row in reader:
        k, v = row
        d[k] = v
    #zipcode conversion
    df_out["location"] = df_out["location"].map(d)
    return df_out

def manipulate_data(df, columns: dict, key_column, contaminants: list, group_columns: list):
    #select only rows with the contaminant we want
    df_out = df[df[key_column].isin(contaminants)]
    #remove the contaminant column, you don't need it anymore
    df_out = df_out.drop(key_column, axis=1)
    #turn all of the dates into year values
    df_out["time"] = pd.DatetimeIndex(pd.to_datetime(df_out["time"])).year
    #average the values per zipcode per year
    df_out = df_out.groupby(group_columns, as_index=False).mean()
    return df_out


def heat_map_adapter(df, year, MRL):
    #adapts data to gmp heatmap input
    #returns exactly what the heatmap function needs
    search = SearchEngine(simple_zipcode=True)
    df_out = df[df["time"] == year]
    df_out = df[df["value"] > MRL]
    #drop null zipcode values
    df_out.replace('', np.nan, inplace=True)
    df_out.dropna(subset=['location'], inplace=True)
    #
    zipcodes = pd.Series(df_out["location"]).to_list()
    zipcodes = [int(zipcode) for zipcode in zipcodes]
    converter = [search.by_zipcode(zipcode) for zipcode in zipcodes]
    lats = [zipcode.to_dict()['lat'] for zipcode in converter if zipcode.to_dict()['lat']]
    longs = [zipcode.to_dict()['lng'] for zipcode in converter if zipcode.to_dict()['lng']]
    #print(lats)
    #print(longs)
    gmap = gmp.GoogleMapPlotter(44.3148, -85.6024, 10)
    gmap.heatmap(lats, longs)
    return gmap



def config():
    with open('config.json') as config_file:
        data = json.load(config_file)
    return data

def main():
    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        print("Please enter the chemical(s) to map \nex: python3 heat_map.py strontium")
        return
    configs = config()
    df = import_data(
        configs["input_file"], \
        configs["zipcode_file"], \
        configs["key_column"],\
        configs["state"], \
        configs["columns"], \
        configs["merge"]
    )
    df = manipulate_data(
        df, \
        configs["columns"],
        configs["key_column"], \
        sys.argv[1:], \
        configs["group_columns"]
    )

    gmap = heat_map_adapter(df, configs["year"], configs["MRL"])
    gmap.draw("%s_heatmap.html" % sys.argv[1])

if __name__ == "__main__":
    main()