# -*- coding: utf-8 -*-
"""
Created on Mon Nov 17 22:22:09 2014

@author: lrousmaniere
"""

#!/usr/bin/env python
 
# Haversine formula example in Python
# Author: Wayne Dyck
 
import math
 
def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km
 
    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c
 
    return d
    
"""
*To run in separate text file...

import Haversine

lat1 = 40.5; lat2 = 42; long1 = -90; long2 = -93
print( Haversine.distance((lat1, long1), (lat2, long2)) )
"""