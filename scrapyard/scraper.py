import base64
import bcode
import binascii
import functools
import newrelic.agent
import network
import random
import requests
import socket
import struct
import sys
import timeit
import urllib
import urlparse
import utils

################################################################################
# Magnet
################################################################################
class Magnet:
    def __init__(self, link, title, seeds, peers, size):
        parse_result = urlparse.parse_qs(urlparse.urlparse(link).query)

        self.link         = link
        self.display_name = parse_result['dn'][0]
        self.title        = title if title else self.display_name
        self.seeds        = seeds
        self.peers        = peers
        self.size         = size
        self.trackers     = map(urlparse.urlparse, parse_result['tr']) if 'tr' in parse_result else []
        self.info_hash    = parse_result['xt'][0].split(':')[-1].upper()

        # Handle Base32-encoded info_hash
        try:
            original       = self.info_hash
            self.info_hash = base64.b16encode(base64.b32decode(self.info_hash))
            self.link      = self.link.replace(original, self.info_hash)
        except:
            pass

################################################################################
# Scraper
################################################################################
def scrape_magnets(magnets, timeout=2):
    # Compile tracker magnet lists
    trackers = {}
    for magnet in magnets:
        for tracker in magnet.trackers:
            if tracker.scheme == 'udp':
                tracker = urlparse.urlparse(urlparse.urlunsplit((tracker.scheme, tracker.netloc, '', '', tracker.fragment)))
            elif tracker.scheme in ['http', 'https']:
                if tracker.path.endswith('announce'):
                    tracker = urlparse.urlparse(tracker.geturl().replace('announce', 'scrape'))
                else:
                    continue

            if tracker not in trackers:
                trackers[tracker] = []

            if magnet not in trackers[tracker]:
                trackers[tracker].append(magnet)

    # Scrape trackers
    tracker_results = dict(utils.mt_map(functools.partial(__scrape_tracker, timeout=timeout), trackers.items()))

    for tracker, tracker_result in tracker_results.iteritems():
        for magnet, magnet_result in tracker_result.iteritems():
            magnet.seeds = max(magnet.seeds, magnet_result['seeds'])
            magnet.peers = max(magnet.peers, magnet_result['peers'])

################################################################################
def __scrape_tracker(tracker_with_magnets, timeout):
    tracker = tracker_with_magnets[0]
    magnets = tracker_with_magnets[1]

    if tracker.scheme == 'udp':
        return (tracker, __scrape_tracker_udp(tracker, magnets, timeout))
    elif tracker.scheme in ['http', 'https']:
        return (tracker, __scrape_tracker_http(tracker, magnets, timeout))

################################################################################
def __scrape_tracker_udp(tracker, magnets, timeout):
    start_time = timeit.default_timer()

    results = {}
    for magnet in magnets:
        results[magnet] = { 'seeds': 0, 'peers': 0, 'completed': 0 }

    if len(magnets) > 74:
        raise RuntimeError("Only 74 hashes can be scraped on a UDP tracker due to UDP limitations")

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        address = (socket.gethostbyname(tracker.hostname), tracker.port if tracker.port else 80)

        # Connection
        send_transaction_id    = random.randint(0, 255)
        send_transaction_data  = struct.pack('!q', 0x41727101980)
        send_transaction_data += struct.pack('!i', 0x0)
        send_transaction_data += struct.pack('!i', send_transaction_id)
        sock.sendto(send_transaction_data, address)

        # Connection response
        recv_transaction_data = sock.recvfrom(2048)[0]
        if len(recv_transaction_data) == 16:
            recv_transaction_action = struct.unpack_from("!i", recv_transaction_data)[0]
            if recv_transaction_action == 0x0:
                recv_transaction_id = struct.unpack_from("!i", recv_transaction_data, 4)[0]
                if send_transaction_id == recv_transaction_id:
                    connection_id = struct.unpack_from("!q", recv_transaction_data, 8)[0]
                    # Scrape
                    send_transaction_id    = random.randint(0, 255)
                    send_transaction_data  = struct.pack('!q', connection_id)
                    send_transaction_data += struct.pack('!i', 0x2)
                    send_transaction_data += struct.pack('!i', send_transaction_id)
                    for magnet in magnets:
                        send_transaction_data += struct.pack('!20s', binascii.a2b_hex(magnet.info_hash))
                    sock.sendto(send_transaction_data, address)
                    # Scrape response
                    recv_transaction_data = sock.recvfrom(2048)[0]
                    if len(recv_transaction_data) >= 16:
                        recv_transaction_action = struct.unpack_from("!i", recv_transaction_data)[0]
                        if recv_transaction_action == 0x2:
                            recv_transaction_id = struct.unpack_from("!i", recv_transaction_data, 4)[0]
                            if send_transaction_id == recv_transaction_id:
                                offset = 8
                                for magnet in magnets:
                                    seeds = struct.unpack_from("!i", recv_transaction_data, offset)[0]
                                    offset += 4
                                    completed = struct.unpack_from("!i", recv_transaction_data, offset)[0]
                                    offset += 4
                                    peers = struct.unpack_from("!i", recv_transaction_data, offset)[0]
                                    offset += 4
                                    results[magnet] = { 'seeds': seeds, 'peers': peers, 'completed': completed }
                                    #sys.stdout.write('{0} : {1:3.1f}s : SCR : {2}://{3} {4}\n'.format('NET:OK', timeit.default_timer() - start_time, tracker.scheme, tracker.netloc, magnet.info_hash))
    except Exception:
        pass

    return results

################################################################################
def __scrape_tracker_http(tracker, magnets, timeout):
    start_time = timeit.default_timer()

    results = {}
    for magnet in magnets:
        results[magnet] = { 'seeds': 0, 'peers': 0, 'completed': 0 }

    query_string = []
    for magnet in magnets:
        query_string.append(("info_hash", binascii.a2b_hex(magnet.info_hash)))
    query_string = urllib.urlencode(query_string)

    url = urlparse.urlunsplit((tracker.scheme, tracker.netloc, tracker.path, query_string, tracker.fragment))

    try:
        http_data = network.http_get(url, timeout=timeout, logging=False)
        if http_data:
            decoded_response = bcode.bdecode(http_data)
            for info_hash, stats in decoded_response['files'].iteritems():
                info_hash = binascii.b2a_hex(info_hash).upper()
                for magnet in results:
                    if magnet.info_hash == info_hash:
                        results[magnet] = { 'seeds': stats['complete'], 'peers': stats['incomplete'], 'completed': stats['downloaded'] }
                        #sys.stdout.write('{0} : {1:3.1f}s : SCR : {2}://{3} {4}\n'.format('NET:OK', timeit.default_timer() - start_time, tracker.scheme, tracker.netloc, magnet.info_hash))
                        break
    except Exception:
        pass

    return results
