# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 18:49:40 2014

@author: lrousmaniere

This script runs against individual polygons.
For multipolygons, please 'explode' the shp into multiple shps using 'Split Layers' in GDAL

Move all of the new files into a single directory, then run the below script against all files
within the directory using bash. i.e. below:

"""

import ogr
import sys
import csv
import Haversine
import math
import os
import re

#argument is shp to be tessellated
fn = sys.argv[1]

#configure for distance between strip center points
buffer = 6.4

if not os.path.isdir('individual_kmls'):
    os.system('mkdir individual_kmls')
if not os.path.isdir('individual_kmls_clipped'):
    os.system('mkdir individual_kmls_clipped')

def get_coordinates(filename):
    driver = ogr.GetDriverByName('ESRI Shapefile')
    dataSource = driver.Open(filename,0)
    # Get Layer
    layer = dataSource.GetLayer(0)
    # Get Features
    feature = layer.GetFeature(0)
    # Get Geometry
    geometry = feature.GetGeometryRef()
    # Get Geometry in Geometry
    ring = geometry.GetGeometryRef(0)
    # Write points in vectors and Textfile
    pointsX = []; pointsY= []; pointsZ = [] # remove pointsZ
    numpoints = ring.GetPointCount() # numbers of points
    
    # create csv
    name = fn[:-4]
    f = open(name +"_coordinates.csv", 'wb')
    writer = csv.writer(f)   
    
    new_list = []
    for p in range(numpoints):
        lon,lat,z = ring.GetPoint(p)
        pointsX.append(lon)
        pointsY.append(lat)
        pointsZ.append(z) # irrelevant
        x = [str(lat),str(lon)]
        writer.writerow(x)
        new_list.append(x)
    return new_list
    dataSource = None

def create_polygon(listed):
    # create ring
    ring = ogr.Geometry(ogr.wkbLinearRing)    
    for lines in listed:        
        ring.AddPoint(float(lines[1]),float(lines[0]))
    poly = ogr.Geometry(ogr.wkbPolygon)
    poly.AddGeometry(ring)
    return poly.ExportToWkt()

def envelope_polygon(polygon):
    shp = str(polygon)
    geom = ogr.CreateGeometryFromWkt(shp)
    env = geom.GetEnvelope()
    return env

def calculate_dist_between_longs(envelope):
    top_lat = envelope[3]
    top_long = envelope[1]
    #bot_lat = envelope[2]
    bot_long = envelope[0]
    lat1 = top_lat
    long1 = top_long
    long2 = bot_long
    return Haversine.distance((lat1, long1), (lat1, long2))

def bottom_lat(envelope):
    return envelope[2]

def top_long_points(envelope,distance):
    dist = calculate_dist_between_longs(envelope)   
    e_long = float(envelope[1])
    w_long = float(envelope[0])
    top_lat = float(envelope[3])
    if e_long < 0 and w_long < 0:
        dist_in_deg = (w_long*-1) - (e_long*-1)
    else:
        dist_in_deg = e_long - w_long
    
    deg_in_km = float(dist_in_deg / dist) #detetime how many degrees 1km is equivalent to
    numb_strips = math.ceil(dist/buffer) #update for strip width
    
    list_top_latlongs = []
    if w_long > 0 and e_long > 0:
        first_long = (w_long + 3.5 * deg_in_km)
        list_top_latlongs.append([top_lat,first_long])
        i = 1
        h = first_long
        while i < numb_strips:
            next_long = h + (deg_in_km*buffer) #7 is configurable        
            list_top_latlongs.append([top_lat,next_long])
            h += (deg_in_km*buffer)           
            i+=1
    else: #getting a little weird here
        first_long = (w_long + 3.5 * deg_in_km)
        list_top_latlongs.append([top_lat,first_long])
        i = 1
        h = first_long
        while i < numb_strips:
            next_long = h + (deg_in_km*buffer) #7 is configurable        
            list_top_latlongs.append([top_lat,next_long])
            h += (deg_in_km*buffer)           
            i+=1
        # may need to update for other negative values
    return list_top_latlongs 

#calculate dist between top and bottom lat
#if dist >50, bottom lat = new lat (top lat - 50km) and create new list of lats
#calculate dist between new lat and bottom lat

def all_lats(list_of_top_lat_longs,bottom_lat):
    top_lat = list_of_top_lat_longs[0][0]
    bottom_lat = bottom_lat
    w_long = list_of_top_lat_longs[0][1]

    dist_between_lats = Haversine.distance((top_lat, w_long), (bottom_lat, w_long))
    if dist_between_lats > 50:
        num_tiers = math.ceil(dist_between_lats/50.0)
    else:
        num_tiers = 1
    
    deg_in_km = float((top_lat - bottom_lat)/ dist_between_lats)
    
    #second_lat = top_lat-(deg_in_km*50)
    list_all_lats = [top_lat]
    k = 1
    while k < num_tiers:
        new_lat = top_lat - (deg_in_km*50)*k
        list_all_lats.append(new_lat)        
        k+=1

    list_all_lats.append(bottom_lat)    
    
    tier_count = len(list_all_lats)
    return list_all_lats,tier_count

def build_csv(envelope,list_top_latlongs,all_lats):
    csv_filename = os.path.basename(fn)[:-4]+"_tessellated.csv"
    f = open(csv_filename, 'wb')
    writer = csv.writer(f)
    writer.writerow(["target_name","customer","order_id","lat","lon","alt","clocking_angle_deg","lat_end","lon_end","alt_end","weight","type","video_duration_s","min_sat_elev_angle_deg","max_sat_elev_angle_deg","min_sat_azim_angle_deg","max_sat_azim_angle_deg"])
    bott_lat = bottom_lat(envelope)
    variables =  all_lats(list_top_latlongs, bott_lat)
    lat_count = variables[1]
    all_longs = []
    for lo in list_top_latlongs:
        longer = lo[1]
        all_longs.append(longer)

    all_lats = variables[0]
    top_list = []
    increment = 0
    while increment < lat_count-1: #HERE'S WHERE WE OMITTED THE LAST LINE
        this_lat = all_lats[increment]
        next_inc = int(increment) + 1
        if next_inc == lat_count:
            next_inc -=1
        that_lat = all_lats[next_inc]        
        for yo in all_longs:
            top_list.append([this_lat,yo,that_lat])
        increment+=1
    list_of_name_and_lon = []
    target = 1
    for i in top_list:
        writer.writerow([os.path.basename(fn)[:-4]+"_"+str(target),"","",i[0],i[1],"0","",i[2],i[1],"0","10","StripCollect","","60","90"])
        list_of_name_and_lon.append([os.path.basename(fn)[:-4]+"_"+str(target),i[1]])
        target +=1
    return csv_filename, list_of_name_and_lon

def convert_csv_to_kml(csv_file):
    os.system('python write_kml_from_csv_external.py -t %s --DontLaunchKML'%csv_file)

def separate_kml_into_separate_kmls(output_kml):
    f = open(output_kml).read()
    placemark_data = f.split("<Placemark>")
    kml_count = 1
    firstitem = True
    for i in placemark_data:
        if firstitem:
            firstitem = False
            continue
        name = re.findall('.*?\<name>(.*?)\</name>.*?', i)[0]
        if "</Document>" in i:
            i = i.replace("</Document>", "")
        if "</kml>" in i:
            i = i.replace("</kml>", "")
        kf = open('individual_kmls/%s.kml'%str(name), 'wb')
        kf.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        kf.write('<kml xmlns="http://www.opengis.net/kml/2.2" xmlns:gx="http://www.google.com/kml/ext/2.2" xmlns:kml="http://www.opengis.net/kml/2.2"\n')
        kf.write('xmlns:atom="http://www.w3.org/2005/Atom">\n')
        kf.write('<Document>\n')
        kf.write('  <name>%s</name>\n'%name)
        kf.write('  <open>1</open>\n')
        kf.write('<Style id="AreaPlot">\n')
        kf.write('  <LineStyle>\n')
        kf.write('      <color>ffffff00</color>\n')
        kf.write('  <width>5.0</width>\n')
        kf.write('  </LineStyle>\n')
        kf.write('  <PolyStyle>\n')
        kf.write('      <fill>0</fill>\n')
        kf.write('  </PolyStyle>\n')
        kf.write('</Style>\n')
        kf.write('  <Placemark>\n')
        kf.write(i + "\n")
        kf.write('</Document>')
        kf.write('</kml>\n')
        ## Done with XML
        kml_count += 1

def clip_kml_to_original_shp(individual_kml):
    new_title = str(individual_kml)[0:-4] + ".kml"
    os.system('ogr2ogr -f "KML" -clipsrc individual_kmls/%s %s %s >/dev/null 2>&1'%(
        str(individual_kml),new_title,fn) )
    os.system('mv %s ./individual_kmls_clipped/'%new_title)

def iterate_over_clipped_kmls_for_top_bottom_lats(clipped_kml):
    f = open(clipped_kml).read()
    if "<coordinates>" not in f: return '',''
    as_string = re.findall('.*?\<coordinates>(.*?)\</coordinates>.*?', f)[0]
    lon_lat_alt = re.split(',| ', as_string)
    lat_list = []
    count = 0
    for value in lon_lat_alt:
        if count == 0:
            count +=1
            continue
        if count == 1:
            lat_list.append(float(value))
            count +=1
            continue
        if count ==2:
            count = 0
            continue
    min_lat = min(lat_list)# + .009 #adding .5km as buffer
    max_lat = max(lat_list)# + .009
    return max_lat, min_lat

def main():
    coords_listed = get_coordinates(fn)
    poly_in_wkt = create_polygon(coords_listed)
    enveloped = envelope_polygon(poly_in_wkt)
    top_line_dist = calculate_dist_between_longs(enveloped)
    list_of_top_lat_longs = top_long_points(enveloped,top_line_dist)
    csv_file, first_lon_list = build_csv(enveloped,list_of_top_lat_longs,all_lats) #use first_lons later
    convert_csv_to_kml(csv_file)
    output_kml = csv_file[0:-4] + ".kml"
    separate_kml_into_separate_kmls(output_kml)
    #All individual kmls are now in individual_kmls dir
    for files in os.listdir('individual_kmls'):
        clip_kml_to_original_shp(files)

    csv_filename = os.path.basename(csv_file)[0:-4] + "_FULL.csv"
    f = open(csv_filename, 'wb')
    writer = csv.writer(f)
    writer.writerow(['target_name','customer','order_id','lat','lon','alt','clocking_angle_deg','lat_end','lon_end',
                     'alt_end','weight','type','video_duration_s','min_sat_elev_angle_deg','max_sat_elev_angle_deg',
                     'min_sat_azim_angle_deg','max_sat_azim_angle_deg','min_solar_zenith_angle_deg',
                     'max_solar_zenith_angle_deg','satellites','start_time','end_time','application_type',
                     'min_cloud_cover','max_cloud_cover'])

    #All individual kmls clipped in individual_kmls_clipped dir
    row = 0
    for clipped_files in os.listdir('individual_kmls_clipped'):
        filename = 'individual_kmls_clipped/' + str(clipped_files)
        #need to pull longitudes from first_lon_list
        start_lat, end_lat = iterate_over_clipped_kmls_for_top_bottom_lats(filename)
        #build decks
        final_lon = 0
        if start_lat:
            final_name = str(clipped_files)[0:-4]
            for rows in first_lon_list:
                if rows[0] == final_name:
                    final_lon = rows[1]
            writer.writerow([str(clipped_files)[0:-4],'','',start_lat,final_lon,0,'',end_lat,final_lon,0,10,'StripCollect','',56,90])
            row +=1

    #os.system("python write_kml_from_csv_external.py -t %s"%csv_filename)
    os.system('rm %s'%str(output_kml))
    #os.system('rm individual_kmls/*')
    #os.system('rm individual_kmls_clipped/*')
    
if __name__== "__main__":
    main()
