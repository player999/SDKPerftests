#!/usr/bin/python3

import sys
import json
import math

def power_entrystats(ventry):
	power_list = []
	for e in ventry["power"]:
		power_list.extend(e)
	return power_stats(power_list)

def power_totalstats(js):
	plist = []
	for entry in js:
		plist.extend(entry["power"])
	power_list = []
	for e in plist:
		power_list.extend(e)
	return power_stats(power_list)

def power_stats(power_list):
	mean = 0
	median = 0
	stdev = 0
	power_list = list(map(lambda x: x[1], power_list))
	mean = sum(power_list) / len(power_list)
	power_list.sort()
	median = power_list[int(len(power_list)/2)]

	acc = 0
	for e in power_list:
		acc = acc + (e - mean) * (e - mean)

	acc = acc / len(power_list)
	std = math.sqrt(acc)

	return mean, median, std

def process_video(ventry):
	print("================================================================================\n")
	print("Path: ", ventry["path"])
	print("Resolution: %dx%d"%(ventry["width"], ventry["height"]))
	print("FPS: ", ventry["fps"])
	mean, median, std = power_entrystats(ventry)
	print("Power mean: %f W" % mean)
	print("Power median: %f W" % median)
	print("Power standart deviation: %f W" % std)
	print("================================================================================\n\n")

def process_file(fname):
	f = open(fname, 'r')
	js = json.load(f)
	f.close()
	for entry in js:
		process_video(entry)

	mean, median, std = power_totalstats(js)
	print("Total power mean: %f W" % mean)
	print("Total power median: %f W" % median)
	print("Total power standart deviation: %f W" % std)
	
if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Wrong arguments!")
		sys.exit(-1)
	process_file(sys.argv[1])