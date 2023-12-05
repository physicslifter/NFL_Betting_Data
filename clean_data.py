"""
Script for cleaning up json files from 
get_data.py
"""
import json
import os
from pandas import DataFrame
from pdb import set_trace as st
import numpy as np

def load_json(fname): #function for loading in json files
    with open(fname) as json_file: #assign opened file to object json_file
        data=json.load(json_file) #load data
    return data

def strip_letters(string):
    letters = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
    for letter in letters:
        string = string.replace(letter, "")
        string = string.replace(letter.upper(), "")
    return string.replace(" ", "")

def strip_numbers(string):
    nums = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]
    for num in nums:
        string = string.replace(num, "")
    return string.replace(" ", "")

def parse_score_string(score_string:str):
    """
    function for parsing string associated with a score
    for ex: ''MIA 23 @ HOU 42''
    """
    away_info, home_info = score_string.split("@")
    away_score, home_score = strip_letters(away_info), strip_letters(home_info)
    away_team, home_team = strip_numbers(away_info), strip_numbers(home_info)
    return {"away_team": away_team, "home_team":home_team, "home_score":home_score, "away_score":away_score}

def get_data(lines_filepath):
    '''
    Gets data for a lines file path
    grabs sister odds filepath
    puts info together
    stores info in dict of depth 1
    '''
    data = load_json(lines_filepath)
    parsed_score = parse_score_string(data["Road v Home"])
    data_dict = {}
    data_dict["Date"] = data["Date"]
    for key in parsed_score.keys():
        data_dict[key] = parsed_score[key]
    for key in data.keys():
        if key not in ["Road v Home", "Date"]:
            if key == "Opening Total":
                opening_val = data[key]
            elif key == "Closing Total":
                data_dict["Opening Total"] = opening_val
                data_dict[key] = data[key]
            else:
                data_dict[key] = data[key]
    odds_data = load_json(lines_filepath.split("_")[0]+"_odds.json")
    for key in odds_data.keys():
        if key not in ["Home Score", "Date"]:
            data_dict[key] = int(odds_data[key].split(" ")[0])
    return data_dict   

def get_all_data():
    lists = {"year":[], "week":[]}
    d = get_data("Data/2015/3/1_lines.json")
    headers = [key for key in d.keys()]
    for header in headers:
        lists[header] = []
    for year in sorted(os.listdir("Data")): #get all years we have data for
        for week in sorted(os.listdir(f"Data/{year}")): #get all weeks we have data for
            valid_files = [f"Data/{year}/{week}/{file}" for file in sorted(os.listdir(f"Data/{year}/{week}")) if "lines" in file]
            for file in valid_files:
                data = get_data(file)
                lists["year"].append(year)
                lists["week"].append(week)
                for header in headers:
                    if header not in data.keys():
                        lists[header].append(np.nan)
                        print(year, week, header, data["home_team"], data["away_team"]) #print out weeks and years and headers that are problematic
                    else:
                        lists[header].append(data[header])
    data_frame = DataFrame(lists)
    data_frame = data_frame.sort_values("Date")
    data_frame.to_excel("Data.xlsx")

test_score_string_parser = 0
test_data_from_lines_file = 0
test_get_all_data = 1

if test_data_from_lines_file == True:
    d = get_data("Data/2015/3/1_lines.json")
    for key in d.keys():
        print(f"{key}: {d[key]}")

if test_score_string_parser == True:
    data = load_json("Data/2017/1/9_lines.json")
    parsed = parse_score_string(data["Road v Home"])
    print(data["Road v Home"])
    for key in parsed.keys():
        print(f"{key}: {parsed[key]}")

if test_get_all_data == True:
    get_all_data()