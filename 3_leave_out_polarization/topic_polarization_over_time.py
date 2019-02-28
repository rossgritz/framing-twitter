#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import division
import pandas as pd
from joblib import Parallel, delayed
import multiprocessing
import json
import sys
import gc
import copy
from calculate_leaveout_polarization import get_leaveout_value
from helper_functions import *


# NOTE: only use this for events where there is enough (temporal) data, otherwise it'll be very noisy

config = json.load(open('../config.json', 'r'))
DATA_DIR = config['DATA_DIR']
TWEET_DIR = config['TWEET_DIR']
NUM_CLUSTERS = config['NUM_CLUSTERS']
events = open(DATA_DIR + 'event_names.txt', 'r').read().splitlines()
event_times = json.load(open(DATA_DIR + "event_times.json","r"))
hour = 60 * 60
day = 24 * hour
split_by = 12 * hour
no_splits = int((day / split_by) * 14)


def get_buckets(data, timestamp):
    '''Divide tweets into time buckets.'''
    timestamps = data['timestamp'].astype(float)
    buckets = []
    start = timestamp
    for i in range(no_splits):
        new_start = start + split_by
        b = copy.deepcopy(data[(timestamps > start) & (timestamps < new_start)])
        start = new_start
        buckets.append(b)
    return buckets

def get_polarization(event, cluster_method = None):
    '''

    :param event: name of the event (str)
    :param cluster_method: None, "relative" or "absolute" (see 5_assign_tweets_to_clusters.py); must have relevant files
    :return: tuple: (true value, random value)
    '''
    data = pd.read_csv(TWEET_DIR + event + '/' + event + '.csv', sep='\t', lineterminator='\n',
                       usecols=['user_id', 'text', 'dem_follows', 'rep_follows'])
    data = filter_clustered_tweets(event, data, TWEET_DIR, cluster_method)
    data['topic'] = get_clusters(event, TWEET_DIR, cluster_method, NUM_CLUSTERS)
    cluster_method = method_name(cluster_method)
    print(event, len(data))

    buckets = get_buckets(data, event_times[event])
    del data
    gc.collect()

    topic_polarization_overtime = {}
    for i, b in enumerate(buckets):
        print('bucket', i)
        topic_polarization = {}
        for j in range(NUM_CLUSTERS):
            print(j)
            topic_polarization[j] = tuple(get_leaveout_value(event, b[b['topic'] == j]))
        topic_polarization_overtime[i] = topic_polarization

    with open(TWEET_DIR + event + '/' + event + '_topic_polarization_overtime' + cluster_method + '.json', 'w') as f:
        f.write(json.dumps(topic_polarization_overtime))

cluster_method = None if len(sys.argv) < 2 else sys.argv[1]

Parallel(n_jobs=3)(delayed(get_polarization)(e, cluster_method) for e in ['orlando', 'vegas', 'parkland'])

