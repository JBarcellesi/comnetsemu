from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import ether_types
from ryu.lib.packet import udp
from ryu.lib.packet import tcp
from ryu.lib.packet import icmp
from ryu.lib import hub

IP_H1="192.0.0.1"



class TrafficSlicing(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(TrafficSlicing, self).__init__(*args, **kwargs)

        # outport = self.mac_to_port[dpid][mac_address]
        self.mac_to_port = {
            1: {"00:00:00:00:00:01": 1, "00:00:00:00:00:02": 2, "00:00:00:00:00:03": 3, "00:00:00:00:00:04":6, "00:00:00:00:00:05":6, "00:00:00:00:00:06":6},
            2: {"00:00:00:00:00:01": 1, "00:00:00:00:00:02": 1, "00:00:00:00:00:03": 1},
            4: {"00:00:00:00:00:07": 4, "00:00:00:00:00:08": 5, "00:00:00:00:00:09": 6},
            5: {"00:00:00:00:00:04": 1, "00:00:00:00:00:05": 2, "00:00:00:00:00:06":3, "00:00:00:00:00:03":4},
        }
        self.slice_TCport = 9999

        # outport = self.slice_ports[dpid][slicenumber]
        self.slice_ports = {1: {1: 4, 2: 4, 3: 5}, 2: {1: 2, 2: 3}, 4: {1: 2, 2: 2, 3: 3}}
        self.end_swtiches = [1, 4]
        self.switch_list=[1, 2, 3, 4, 5]
       # self.updateRules_thread = hub.spawn(self.updateRules)

    #def updateRules(self):
    #    while True:
    #        hub.sleep(3)
    #        for id in self.switch_list:
    #            self.send_table_stats_request(self.switch_list[id])
    #        hub.sleep(3)
    #    def send_table_stats_request(self, datapath):
    #        ofp_parser = datapath.ofproto_parser
    #        req = ofp_parser.OFPTableStatsRequest(datapath, 0)
    #        datapath.send_msg(req)
        
    #    @set_ev_cls(ofp_event.EventOFPTableStatsReply, MAIN_DISPATCHER)
    #    def table_stats_reply_handler(self, ev):
    #        tables = []
    #        for stat in ev.msg.body:
    #            tables.append('table_id=%d active_count=%d lookup_count=%d '
    #                      ' matched_count=%d' %
    #                      (stat.table_id, stat.active_count,
    #                       stat.lookup_count, stat.matched_count))
    #        for t in tables:
    #            print(tables[t])
            #self.logger.debug('TableStats: %s', tables)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
	#handshake controller-switch
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # install the table-miss flow entry.
        match = parser.OFPMatch()
        actions = [
            parser.OFPActionOutput(ofproto.OFPP_CONTROLLER, ofproto.OFPCML_NO_BUFFER)
        ]
        self.add_flow(datapath, 0, match, actions)

	
    def add_flow(self, datapath, priority, match, actions):
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        # construct flow_mod message and send it.
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath=datapath, priority=priority, match=match, instructions=inst
        )
        datapath.send_msg(mod)

    def _send_package(self, msg, datapath, in_port, actions):
        data = None
        ofproto = datapath.ofproto
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = datapath.ofproto_parser.OFPPacketOut(
            datapath=datapath,
            buffer_id=msg.buffer_id,
            in_port=in_port,
            actions=actions,
            data=data,
        )
        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        in_port = msg.match["in_port"]

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            # ignore lldp packet
            return
        dst = eth.dst
        src = eth.src
        
        ip=pkt.protocols[1]
        ip_dst=ip.dst
        ip_src=ip.src



        dpid = datapath.id

        if dpid in self.mac_to_port :
            if dst in self.mac_to_port[dpid]:
                out_port = self.mac_to_port[dpid][dst]
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                match = datapath.ofproto_parser.OFPMatch(eth_dst=dst)
                self.add_flow(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

            elif (pkt.get_protocol(udp.udp)):
                slice_number = 1
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x11,  # udp
                    udp_dst=self.slice_TCport,
                )

                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, 2, match, actions)
                self._send_package(msg, datapath, in_port, actions)

            elif pkt.get_protocol(tcp.tcp) and (ip_dst== IP_H1 or ip_src== IP_H1):
                slice_number = 3
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x06,  # tcp
                )
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

            elif pkt.get_protocol(tcp.tcp):
                slice_number = 2
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x06,  # tcp
                )
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

            elif pkt.get_protocol(icmp.icmp):
                slice_number = 1
                out_port = self.slice_ports[dpid][slice_number]
                match = datapath.ofproto_parser.OFPMatch(
                    in_port=in_port,
                    eth_dst=dst,
                    eth_src=src,
                    eth_type=ether_types.ETH_TYPE_IP,
                    ip_proto=0x01,  # icmp
                )
                actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
                self.add_flow(datapath, 1, match, actions)
                self._send_package(msg, datapath, in_port, actions)

        elif dpid not in self.end_swtiches:
            out_port = ofproto.OFPP_FLOOD
            actions = [datapath.ofproto_parser.OFPActionOutput(out_port)]
            match = datapath.ofproto_parser.OFPMatch(in_port=in_port)
            self.add_flow(datapath, 1, match, actions)
            self._send_package(msg, datapath, in_port, actions)