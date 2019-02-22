from interrogator import *
import threading
import json
import sys
from httplib2 import Http
from sllurp import *
from sllurp.llrp import *
from twisted.internet import reactor
import os
import Queue
from time import sleep
import collections

# sllurp, llrp_proto GPLv2 statement:
# Copyright (C) 2009 Rodolfo Giometti <giometti@linux.it>
# Copyright (C) 2009 CAEN RFID <support.rfid@caen.it>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


class ImpinjR420(Interrogator):
    def __init__(self, _ip_address, _db_host, _db_password, _cert_path, _debug, _dispatchsleep=0, _antennas=[], _channellist=[], _tagpop=16):
        Interrogator.__init__(self, _db_host, _db_password,
                              _cert_path, _debug, _dispatchsleep)
        self.exiting = False
        self.ip_address = _ip_address
        if len(_antennas) > 0:
            self.antennas = _antennas
        else:
            self.antennas = [1, 2, 3, 4]
        self.channellist = _channellist  # empty channel list defaults to all channels
        self.tagpop = _tagpop

        if self.cert_path != 'NONE':
            self.http_obj = Http(ca_certs=self.cert_path)
        else:
            self.http_obj = Http(disable_ssl_certificate_validation=True)

        self.out('Initializing R420 interrogator client')

    def out(self, x):
        if self.debug:
            sys.stdout.write(str(x) + '\n')

    def start_server(self):
        self.out('Starting Impinj R420 interrogator client')

        # Create Clients and set them to connect
        self.fac = LLRPClientFactory(report_every_n_tags=1,  # report every N>1 tags so that it reports more slowly to avoid lag; note this results in packets not sampled by the Impinj and only every 2 tags are reported, which it notes in TagSeenCount and the difference between FirstSeenTimestamp and LastSeenTimestamp; set PeriodicTriggerValue to something like 50 to group transmissions (will have to loop over messages received here), and set ROSpecStartTriggerType to 2 == Periodic
                                     # 0 = all antennae but might not get configured by ROSpec unless explicitly enumerated
                                     antennas=self.antennas,
                                     tx_power=81,  # was 0, 81 is 30 dbm, 91 is max 32.5 dbm
                                     modulation='M4',  # FM0 max throughput, M8/M4 alternative
                                     ntari=0,
                                     session=2,  # was 2
                                     start_inventory=True,
                                     tag_population=self.tagpop,  # The interrogator can only handle 90 reads per second over ethernet; if the read rate is greater than this, only 90 per second will be processed, up to 5000 per minute.  If 5000 tags is reached before one minute's time, lag will be introduced as a shorter amount of time will be obtained.  Setting to tag population of 16 enables 2 tags; tag population of 4 is best for 1 tag.  Best to parameterize this
                                     mode_index=2,  # 0 = max throughput, could do hybrid mode 1 or maxmiller 4, dense 8 == 3, dense 4 == 2
                                     channellist=self.channellist,
                                     # convert to integer milliseconds
                                     periodictrigger=int(
                                         self.dispatchsleep * 1000),
                                     tag_content_selector={
                                         'EnableROSpecID': True,
                                         'EnableSpecIndex': True,
                                         'EnableInventoryParameterSpecID': True,
                                         'EnableAntennaID': True,
                                         'EnableChannelIndex': True,
                                         'EnablePeakRRSI': True,  # does not appear to be a typo
                                         'EnableFirstSeenTimestamp': True,
                                         'EnableLastSeenTimestamp': True,
                                         'EnableTagSeenCount': True,
                                         'EnableAccessSpecID': True,
                                     })

        self.fac.addTagReportCallback(self.handle_event)

        self.out('Starting Reactor TCP client')

        reactor.connectTCP(self.ip_address, 5084, self.fac, timeout=5)
        reactor.run()

    def communication_consumer(self):
        url = self.db_host + '/api/rssi'

        while not self.exiting:
            input_dicts = []

            input_dict = self.tag_dicts_queue.get(block=True)
            input_dicts.append(input_dict)

            # http://stackoverflow.com/questions/156360/get-all-items-from-thread-queue
            # while we're here, try to pick up any more items that were inserted into the queue
            while 1:
                try:
                    input_dict = self.tag_dicts_queue.get_nowait()
                    input_dicts.append(input_dict)
                except Queue.Empty:
                    break

            resp, content = self.http_obj.request(uri=url, method='PUT', headers={
                                                  'Content-Type': 'application/json; charset=UTF-8'}, body=json.dumps(input_dicts))

            if self.dispatchsleep > 0:
                # if desired, sleep the dispatcher for a short time to queue up some inserts and give the producer some CPU time
                sleep(self.dispatchsleep)

    def start(self):
        self.out('R420: start')

        self.handler_dequeue = collections.deque()
        self.handler_thread = threading.Thread(
            target=self.handler_thread, args=())
        self.handler_thread.start()

        self.tag_dicts_queue = Queue.Queue()
        self.communication_thread = threading.Thread(
            target=self.communication_consumer, args=())
        self.communication_thread.start()

        self.start_server()

    def handle_event(self, msg):
        self.handler_dequeue.append(msg)

    def handler_thread(self):
        while not self.exiting:
            if len(self.handler_dequeue) == 0:
                if self.dispatchsleep > 0:
                    sleep(self.dispatchsleep)
                continue

            input_msgs = []

            input_msg = self.handler_dequeue.popleft()
            input_msgs.append(input_msg)

            # Subtags like <EPC> may or may not be present
            # <RO_ACCESS_REPORT>
            #    <Ver>1</Ver>
            #    <Type>61</Type>
            #    <ID>2323</ID>
            #    <TagReportData>
            #        <EPC-96>
            #            <EPC>00e200600312226a4b000000</EPC>
            #        </EPC-96>
            #        <Antenna>
            #            <Antenna>0001</Antenna>
            #        </Antenna>
            #        <RSSI>
            #            <RSSI>ba</RSSI>
            #        </RSSI>
            # .... also a Timestamp here
            #   and now, with impinj extensions and sllurp
            #    <RFPhaseAngle>1744</RFPhaseAngle>
            #    <Doppler>234</Doppler>
            #    </TagReportData>
            # </RO_ACCESS_REPORT>

            for msg in input_msgs:
                self.out(msg)

                tags = msg.msgdict['RO_ACCESS_REPORT']['TagReportData']

                self.out(tags)

                for tag in tags:
                    if 'FirstSeenTimestampUTC' in tag and 'EPC-96' in tag and 'AntennaID' in tag and 'PeakRSSI' in tag:
                        first_seen_timestamp = tag['FirstSeenTimestampUTC'][0]
                        epc96 = tag['EPC-96']
                        antenna = tag['AntennaID'][0]
                        rssi = tag['PeakRSSI'][0]
                    else:
                        self.out(
                            "Message did not contain all elements\n" + str(tag))
                        continue

                    # Optional parameters from sllurp library for Impinj
                    if 'Doppler' in tag:
                        doppler = tag['Doppler']
                    else:
                        doppler = "-65536"

                    if 'RFPhaseAngle' in tag:
                        phase = tag['RFPhaseAngle']
                    else:
                        phase = "-65536"

                    if 'ROSpecID' in tag:
                        rospecid = tag['ROSpecID'][0]
                    else:
                        rospecid = "-1"

                    if 'ChannelIndex' in tag:
                        channelindex = tag['ChannelIndex'][0]
                    else:
                        channelindex = "-1"

                    if 'TagSeenCount' in tag:
                        tagseencount = tag['TagSeenCount'][0]
                    else:
                        tagseencount = "-1"

                    if 'LastSeenTimestampUTC' in tag:
                        lastseentimestamp = tag['LastSeenTimestampUTC'][0]
                    else:
                        lastseentimestamp = "-1"

                    if 'AccessSpecID' in tag:
                        accessspecid = tag['AccessSpecID'][0]
                    else:
                        accessspecid = "-1"

                    if 'InventoryParameterSpecID' in tag:
                        inventoryparameterspecid = tag['InventoryParameterSpecID'][0]
                    else:
                        inventoryparameterspecid = "-1"

                    self.count = self.count + 1

                    # if this is the "first" firstseentimestamp, note that so the other times will be relative to that
                    if self.start_timestamp == 0:
                        self.start_timestamp = first_seen_timestamp

                    self.latest_timestamp = first_seen_timestamp

                    # call self.insert_tag to insert into database
                    self.insert_tag(epc96, antenna, rssi, doppler, phase, first_seen_timestamp, rospecid, channelindex,
                                    tagseencount, lastseentimestamp, accessspecid, inventoryparameterspecid, self.start_timestamp)

    def close_server(self):
        self.exiting = True
        reactor.stop()
        if not (self.fac is None):
            if not (self.fac.proto is None):
                self.fac.proto.exiting = True

    def __del__(self):
        self.close_server()

    def insert_tag(self, epc, antenna, peak_rssi, doppler, phase, first_seen_timestamp, rospecid, channelindex, tagseencount, lastseentimestamp, accessspecid, inventoryparameterspecid, start_timestamp):
        if peak_rssi >= 128:  # convert to signed
            peak_rssi = peak_rssi - 256

        self.out("Adding tag %s with RSSI %s and timestamp %s and ID %s on antenna %s with Phase %s and Doppler %s and Channel %s" % (
            str(self.count), str(peak_rssi), str(first_seen_timestamp), str(epc), str(antenna), str(doppler), str(phase), str(channelindex)))

        input_dict = dict()
        input_dict['data'] = dict()
        input_dict['data']['db_password'] = self.db_password
        input_dict['data']['rssi'] = peak_rssi
        input_dict['data']['relative_time'] = first_seen_timestamp - \
            start_timestamp
        input_dict['data']['interrogator_time'] = first_seen_timestamp
        input_dict['data']['epc96'] = epc
        input_dict['data']['antenna'] = antenna
        input_dict['data']['doppler'] = doppler
        input_dict['data']['phase'] = phase
        input_dict['data']['rospecid'] = rospecid
        input_dict['data']['channelindex'] = channelindex
        input_dict['data']['tagseencount'] = tagseencount
        input_dict['data']['lastseentimestamp'] = lastseentimestamp
        input_dict['data']['accessspecid'] = accessspecid
        input_dict['data']['inventoryparameterspecid'] = inventoryparameterspecid

        self.tag_dicts_queue.put(input_dict)  # read by the consumer


# Requires:
# easy_install httplib2 (not pip)