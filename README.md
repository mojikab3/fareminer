# Fare Miner
This Python script is designed to fetch flight data, both domestic and international, including flight distances, fares, and more from __respina24__

## Prerequisites

- Python 3.x
- Internet connectivity for web data retrieval

## Installation

1. Clone the repository:
```bash
git clone https://github.com/mojikab3/fareminer.git
```
2. Go to the repository directory:
  ```bash
  cd ./fareminer
  ```
3. Install the required libraries
  ```bash
  pip install -r requirements.txt
  ```
4. Execute the script
  ```bash
  python ./fareminer.py
  ```

## Usage
To get help
```bash
python ./fareminer.py -h
```
To get the domestic flight data 
```bash
python ./fareminer.py -d [Departure IATA code] [Arrival IATA code] -s [Start date] -e [End date]
```
For example this command gets the flight data for Tehran-Tabriz route from 2023-11-3 to 2023-11-18
```bash
python ./fareminer.py -d thr tbz -s 2023-11-3 -e 2023-11-18
```
To get the international flight data use -i instead of -d. leave the end date if you want to get the data for just a day instead of a period. you can change the output file name with -o 
```bash
python ./fareminer.py -i fra ika -s 2023-11-2
```
The mined data gets exported into a csv file which you can import into excell or google sheets or analyze it using pandas

