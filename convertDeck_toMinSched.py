import csv, datetime, os, sys

filename = sys.argv[1]

satellite_conversion = {
    "SS-1":"0001",
    "SS-2":"0002",
    "SS-C1":"0003",
    "SS-C2":"0004",
    "SS-C3":"0067",
    "SS-C4":"0068",
    "SS-C5":"0069"
}

def read_csv(filename):
    f = open(filename, 'rb')
    reader = csv.DictReader(f)
    return reader

def list_of_headers(filename):
    reader = csv.reader(open(filename, 'rb'))
    list_of_headers = []
    for i in reader:
        list_of_headers.append(i)
        break
    if "satellites" not in list_of_headers[0] or "start_time" not in list_of_headers[0] or "end_time" not in list_of_headers[0]:
        print "\nError!\nEither 'satellites', 'start_time', or 'end_time' field not in list of headers\n"
        sys.exit()
    return list_of_headers[0]

def convert_sats_and_times(dict_of_values):

    """Update satellites below"""
    satellites = dict_of_values["satellites"]
    new_satellites = ""
    for sats in satellites.split():
        if sats in satellite_conversion:
            sats = satellite_conversion[sats]
            new_satellites += str(" " + sats)
    new_satellites = new_satellites[1:] #to remove the first space
    dict_of_values["satellites"] = new_satellites

    """Update start / end times to GPS micro-seconds below"""
    start_time = datetime.datetime.strptime( dict_of_values["start_time"], "%Y%m%dT%M%S%fZ")
    end_time = datetime.datetime.strptime( dict_of_values["end_time"], "%Y%m%dT%M%S%fZ")
    gps_start_date = datetime.datetime(1980,1,6)
    start_gps = int( (start_time - gps_start_date).total_seconds() )
    end_gps = int ((end_time - gps_start_date).total_seconds() )

    #update to string
    dict_of_values["start_time"] = str(start_gps) + "0000"
    dict_of_values["end_time"] = str(end_gps) + "0000"

    return dict_of_values

def main():
    csv_title = os.path.basename(filename)[:-4] + "_minSchedFormat.csv"
    headers = list_of_headers(filename)
    f = open(csv_title, 'wb')
    writer = csv.DictWriter(f, fieldnames=headers)
    writer.writeheader()
    for i in read_csv(filename):
        updated_values = convert_sats_and_times(i)
        writer.writerow(updated_values)

if __name__ == "__main__":
    main()
