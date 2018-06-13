import matplotlib.pyplot as plt
import numpy as np
import png
import pickle
import random

# import shapely

from shapely.geometry import LineString
# from skimage import feature
# from pympler import asizeof
# from pathfinding.core.grid import Grid
from networkx.algorithms.shortest_paths.astar import astar_path
from networkx import Graph
from networkx.exception import NetworkXNoPath

from .osmhandler import *
from .illustrator import Illustrator
from .pathfinder import Pathfinder


class WayMap:
    def __init__(self, map_file):
        self.map_file = map_file

        self.handler = OSMHandler(self.map_file)
        self.handler.apply_file(self.map_file, locations=True)
        self.way_list = self.handler.way_list
        self.minlat = self.handler.minlat
        self.minlon = self.handler.minlon
        self.maxlat = self.handler.maxlat
        self.maxlon = self.handler.maxlon
        
        self.graph = Graph(WayGraph(self.way_list))

    def save_as_png(self, filename):
        size = ((self.maxlon - self.minlon) * 400, (self.maxlat - self.minlat) * 400)
        print(size)
        fig = plt.figure(frameon=False, figsize=size)
        subplot = fig.add_subplot(111)
        fig.subplots_adjust(bottom = 0)
        fig.subplots_adjust(top = 1)
        fig.subplots_adjust(right = 1)
        fig.subplots_adjust(left = 0)
        subplot.set_xlim((self.minlon, self.maxlon))
        subplot.set_ylim((self.minlat, self.maxlat))
        subplot.axis("off")
        subplot.tick_params(axis="both", which="both", left=False, top=False, right=False, bottom=False, labelleft=False,
                            labeltop=False, labelright=False, labelbottom=False, length=0, width=0, pad=0)
        for e in self.way_list:
            if e.category == "walkway":
                subplot.plot(list(e.line.xy[0]), list(e.line.xy[1]), color="black", aa=False, linewidth=0.1)
            elif e.category == "crossing":
                subplot.plot(list(e.line.xy[0]), list(e.line.xy[1]), color="black", aa=False, linewidth=0.1)
            elif e.category == "steps":
                subplot.plot(list(e.line.xy[0]), list(e.line.xy[1]), color="black", aa=False, linewidth=0.1)
        plt.gca().xaxis.set_major_locator(plt.NullLocator())
        plt.gca().yaxis.set_major_locator(plt.NullLocator())
        # plt.autoscale(tight=False, enable=False)
        plt.savefig(filename, dpi=100, bbox_inches="tight", pad_inches=0)

    def save_part_as_png(self, filename, partial_bounds):
        partial_minlon, partial_maxlon = partial_bounds[0], partial_bounds[1]
        partial_minlat, partial_maxlat = partial_bounds[2], partial_bounds[3]
        if (partial_minlon > self.minlon or partial_maxlon > self.maxlon or 
            partial_minlat > self.minlat or partial_maxlat > self.maxlat):
            raise ValueError("partial_bounds out of WayMap's bounds")



class WorkRun():
    """docstring for WorkRun"""
    def __init__(self,
                 bounds=None,
                 osm_file=None,
                 num_of_chunks=1,
                 chunk_size=None,
                 num_of_trips=1,
                 origin_choice="random",
                 destination_choice="random",
                 allowed_means_of_transport="walking",
                 database=None):
        super(WorkRun, self).__init__()
        self.bounds = bounds
        self.osm_file = osm_file
        self.num_of_chunks = num_of_chunks
        self.chunk_size = chunk_size
        self.num_of_trips = num_of_trips
        self.origin_choice = origin_choice
        self.destination_choice = destination_choice
        self.allowed_means_of_transport = allowed_means_of_transport
        self.database = database

        self.chunks = []

        for i in range(num_of_chunks):
            way_map = WayMap(self.osm_file)
            chunk = Chunk(way_map, trips=[], num_of_trips=self.num_of_trips)
            points_list = list(way_map.graph)
            if len(points_list) < 2:
                raise ValueError("Not enough points on map")
            # trips = []
            for trip in range(self.num_of_trips):
                start, end = random.sample(points_list, 2)
                chunk.trips.append(Trip(way_map, start, end))
            self.chunks.append(chunk)

class Chunk(object):
    """docstring for Chunk"""
    def __init__(self, way_map, trips=[], num_of_trips=1):
        super(Chunk, self).__init__()
        self.way_map = way_map
        self.trips = trips
        self.num_of_trips = num_of_trips
        

class Trip():
    """docstring for Trip"""
    def __init__(self, way_map, start, end):
        super(Trip, self).__init__()
        self.way_map = way_map
        self.start = start
        self.end = end
        self.path = Path(self.way_map, self.start, self.end)
        if len(self.path) >= 2:
            self.is_traversible = True
        else:
            self.is_traversible = False
        

class Path(LineString):
    """docstring for Path"""
    def __init__(self, way_map, start, end):
        super(Path, self).__init__()
        self.way_map = way_map
        self.start = start
        self.end = end
        try:
            self.list_of_nodes = astar_path(self.way_map.graph, self.start, self.end)
        except NetworkXNoPath:
            self.list_of_nodes = []
        self.linestring = LineString(self.list_of_nodes)
    def __len__(self):
        return len(self.list_of_nodes)
           

class WayGraph(dict):
    """docstring for WayGraph"""
    def __init__(self, way_list):
        super(WayGraph, self).__init__()
        self.way_list = way_list
        for way in self.way_list:
            linestring = way.line
            category = way.category
            x = linestring.coords.xy[0]
            y = linestring.coords.xy[1]
            for i in range(len(x)):
                xy = (x[i], y[i])
                if i == 0:
                    if xy not in self:
                        self[xy] = [(x[i + 1], y[i + 1])]
                    else:
                        self[xy].append((x[i + 1], y[i + 1]))
                elif i == len(x) - 1:
                    if xy not in self:
                        self[xy] = [(x[i - 1], y[i - 1])]
                    else:
                        self[xy].append((x[i - 1], y[i - 1]))
                else:
                    if xy not in self:
                        self[xy] = [(x[i + 1], y[i + 1]), (x[i - 1], y[i - 1])]
                    else:
                        self[xy].append((x[i + 1], y[i + 1]))
                        self[xy].append((x[i - 1], y[i - 1]))


def paths_adder(way_map, num_of_paths, walking_function):
    holder_array = np.zeros_like(way_map.array, dtype="B")
    for i in range(num_of_paths):
        print("path: ", i)
        new_path = Illustrator.draw_walked_path(way_map, walking_function)
        np.add(holder_array, new_path, out=holder_array)
    return holder_array
    pass


if __name__ == '__main__':

    pass