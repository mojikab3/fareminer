import requests, csv, pytz, re, json, argparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
from jdatetime import datetime as jdatetime


# Converts gregorian dates to jalali
def ToJalali(date_time):
    jalali_date = jdatetime.fromgregorian(datetime=date_time)
    return jalali_date.strftime('%Y/%m/%d %H:%M')


# Generates a list of dates
def GetDates(start, end):
    dates = []
    if end is None:
        return [start]
    
    start_date = datetime.strptime(start, '%Y-%m-%d')
    end_date = datetime.strptime(end, '%Y-%m-%d')
    current_date = start_date
    
    while current_date <= end_date:
        dates.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)

    return dates


def Error():
    raise ValueError("Sorry, there's a problem")


# Gets the distance between the departure airport and arrival airport in kilometers
def GetFlightDistance(departure_airport, arrival_airport):
    
    url = f'https://www.airportdistancecalculator.com/flight-{departure_airport}-to-{arrival_airport}.html'
    
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')

        distance_element = soup.find('strong', string=re.compile(r'\d+ kilometers'))

        if distance_element:
            distance_text = distance_element.get_text()
            distance_in_km = re.search(r'(\d+) kilometers', distance_text).group(1)
            return distance_in_km
        else:
            Error()
    else:
        Error()


# Converts local datetime to GMT datetime
def GetGMTDateTime(city_name, local_datetime):
    try:
        geolocator = Nominatim(user_agent="city_timezone_lookup")
        try:
            location = geolocator.geocode(city_name, timeout=10)
        except GeocoderTimedOut:
            print("Geocoding service timed out. try again")
        if location:
            tz_finder = TimezoneFinder()
            local_timezone_str = tz_finder.timezone_at(lng=location.longitude, lat=location.latitude)
            local_timezone = pytz.timezone(local_timezone_str)

            gmt_datetime = local_datetime.astimezone(pytz.utc)

            return gmt_datetime
        else:
            Error()
    except pytz.exceptions.UnknownTimeZoneError:
        return "Unknown time zone for the city"


# Fetches US dollar rate
def GetExchangeRate():
    url = "https://tgju.org/profile/price_dollar_rl"
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        script = soup.find('script', string=re.compile('chartData: \[\[.*\]\]'))
        
        if script:
            script_text = script.string
            chart_data_match = re.search(r'chartData: (\[\[.*\]\])', script_text)
            
            if chart_data_match:
                chart_data_json = chart_data_match.group(1)
                chart_data = json.loads(chart_data_json)
                
                if chart_data:
                    return chart_data[-1][-1]


# Gets flight fares for domestic routes
def GetDomesticFare(origin, destination, rate=50000, date=str(datetime.now().date()), output=None):
    
    print(f'Getting the data for {origin} => {destination}')
    
    if output is None: 
        output = origin + '_' + destination + '_' + str(datetime.now().date())
    url = "https://respina24.ir/flight/availability"
    
    headers = {
        "Content-Type": "application/json",
    }
    
    payload = {
        "from": origin,
        "to": destination,
        "departureDate": date,
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        itineraries = data.get('list', [])
        distance = GetFlightDistance(origin, destination) 
        with open(output + '.csv', 'a', newline='') as csvfile:
            fieldnames = ['From', 'To', 'Total Time',
                        'Total Distance (km)', 'Class',
                        'Departure Date and Time', 'Arrival Date and Time',
                        'Aircraft', 'Airline',
                        'Cost (Toman)', 'Cost (USD)', 'USD to Toman Rate']
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            if csvfile.tell() == 0:
                writer.writeheader()
         
            for itinerary in itineraries:
                fare = itinerary.get('adultPrice')
                airline = itinerary.get('airlineName')
                aircraft = itinerary.get('aircraft')
                cabin = itinerary.get('cobin') + ' ' + itinerary.get('class')
                departureDatetime = datetime.strptime(itinerary.get('departureDate') + ' ' + itinerary.get('departureTime'), '%Y-%m-%d %H:%M') 
                arrivalDatetime = datetime.strptime(itinerary.get('departureDate') + ' ' + itinerary.get('arrivalTime'), '%Y-%m-%d %H:%M') 
                flightDuration = itinerary.get('flightDuration') 
                
                writer.writerow({
                    'From': origin,
                    'To': destination,
                    'Total Time': flightDuration,
                    'Total Distance (km)': distance,
                    'Class': cabin,
                    'Departure Date and Time': ToJalali(departureDatetime),
                    'Arrival Date and Time': ToJalali(arrivalDatetime),
                    'Aircraft': aircraft, 
                    'Airline': airline,
                    'Cost (Toman)': fare / 10,  
                    'Cost (USD)': '{:.2f}'.format(fare / int(rate)),
                    'USD to Toman Rate': rate / 10,  
                })
                
    else:
        print('Failed to retrieve flight data. Status code:', response.status_code)
    

# Gets flight fares for international routes
def GetInterFare(origin, destination, rate=50000, date=str(datetime.now().date()), output=None):
    
    print(f'Getting the data for {origin} => {destination}')
    print(f'Press Ctrl + D to stop the script if you\'re happy with the results')
    
    if output is None: 
        output = origin + '_' + destination + '_' + str(datetime.now().date())
    firstUrl = "https://respina24.ir/internationalflight/getFlightAjax"
    secondUrl = "https://respina24.ir/internationalflight/getFlightAjax2"
    thirdUrl = "https://respina24.ir/internationalflight/getFlightAjaxPagination"
 
    headers = {
        "Content-Type": "application/json;charset=UTF-8",
    }
    distance = GetFlightDistance(origin, destination) 
    cabinTypes = ["1", "3", "5"]
    for cabinType in cabinTypes:
            
        firstPayload = {
            "adult":"1",
            "child":"0",
            "infant":"0",
            "cabinType":cabinType,
            "tripType":"1",
            "itineries":[{
                "from":origin,"to":destination,
                "date":date,
                "fromIsCity":1,"toIsCity":1}],
            "cache":"1",
            "indexFlight":0,
            "searchId":0
        }
        
        apiIds = [str(i) for i in range(1, 13)]
        response = requests.post(firstUrl, headers=headers, json=firstPayload)
        if response.status_code == 200:
            data = response.json()
            search_id = data.get('search_id')
            
            for apiId in apiIds:
                secondPayload = {
                    "api_id": apiId,
                    "api_name": "api",
                    "search_id": search_id
                } 
            
                secondResponse = requests.post(secondUrl, json=secondPayload, headers=headers)
                    
            if secondResponse.status_code == 200: 
                for stop in range(2):
                    thirdPayload = {
                        "searchId": search_id,
                        "page": 1,
                        "filter": {
                            "outboundStops": [
                                str(stop)
                            ]
                        }
                    } 
                    
                    thirdResponse = requests.post(thirdUrl, json=thirdPayload, headers=headers)
                    
                    data = thirdResponse.json()
                    flights = data.get('flights', [])
                    with open(output + '.csv', 'a', newline='') as csvfile:
                        fieldnames = ['From', 'Stop', 'To', 'Total Time',
                                    'Total Distance (km)', 'Class',
                                    'Departure Date and Time (GMT)', 'Arrival Date and Time (GMT)',
                                    'Aircraft', 'Airline', 'Flight Number',
                                    'Cost (Toman)', 'Cost (USD)', 'USD to Toman Rate']
                    
                        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                        if csvfile.tell() == 0:
                            writer.writeheader()
                        
                        for flight in flights:
                            masir = flight.get('masir', [])
                            legs = masir[0].get('legs', [])
                            outboundStops = flight.get('outboundStops')
                            
                            fare = flight.get('adultPrice')
                            cabin = legs[0].get('cabinTypeValue') 
                            airline = masir[0].get('AirlineName')
                            duration = masir[0].get('JourneyDuration')
                            flightNumbers = masir[0].get('flightNumbers')
                            
                            departureCity = masir[0].get('fromCityName')
                            departureAirport = masir[0].get('from')
                            departureDateTime = masir[0].get('DepartureDateTime') 
                            
                            if outboundStops == 1:
                                stopCity = legs[0].get('toCityName')
                                stopAirport = legs[0].get('to')
                                stopString = stopCity + '(' + stopAirport + ')'
                            else: 
                                stopString = ''
                                
                            arrivalCity = masir[0].get('to')
                            arrivalAirport = masir[0].get('toCityName') 
                            arrivalDateTime = masir[0].get('ArrivalDateTime') 
                            writer.writerow({
                                'From': departureCity + '(' + departureAirport + ')',
                                'Stop': stopString,
                                'To': arrivalCity + '(' + arrivalAirport + ')',
                                'Total Time': duration,
                                'Total Distance (km)': distance,
                                'Class': cabin,
                                'Departure Date and Time (GMT)': GetGMTDateTime(departureCity, datetime.fromisoformat(departureDateTime)),
                                'Arrival Date and Time (GMT)': GetGMTDateTime(arrivalCity , datetime.fromisoformat(arrivalDateTime)),
                                'Aircraft': '', 
                                'Flight Number': flightNumbers,
                                'Airline': airline,
                                'Cost (Toman)': fare / 10,  
                                'Cost (USD)': '{:.2f}'.format(fare / int(rate)),
                                'USD to Toman Rate': rate / 10,  
                            })
            else:
                print("getFlightAjax2 Failed")    
        else:
            print("getFlightAjax Failed")
        

if __name__ == '__main__':   
    parser = argparse.ArgumentParser()
    parser.add_argument('origin', type=str, help='Departure city IATA code like THR, TBZ')
    parser.add_argument('destination', type=str, help='Arrival city IATA code like THR, TBZ')
    parser.add_argument('--domestic', '-d', action='store_true', help='Get fares for domestic flights')
    parser.add_argument('--international', '-i', action='store_true', help='Get fares for internationl flights')
    parser.add_argument('--start', '-s', type=str, help='Date range start (2023-10-18) (leave emtpy for getting today\' flights )')
    parser.add_argument('--end', '-e', type=str, help='Date range end (2023-10-20) (leave it if you want to get the fares only on the start date)')
    parser.add_argument('--output', '-o', type=str, help='output path')
    args = parser.parse_args()

    if args.domestic:
        dates = GetDates(args.start, args.end)
        for date in dates:
            GetDomesticFare(args.origin, args.destination, rate=GetExchangeRate(), date=date, output=args.output)
            
    elif args.international:
        dates = GetDates(args.start, args.end)
        for date in dates:
            GetInterFare(args.origin, args.destination, rate=GetExchangeRate(), date=date, output=args.output)
    else:
        print("Determine your flight type (international/domestic)")