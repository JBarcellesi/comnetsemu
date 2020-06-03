#!/usr/bin/python3

import os

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import OVSKernelSwitch, RemoteController
from comnetsemu.cli import CLI, spawnXtermDocker
from mininet.link import TCLink
from mininet.log import info, setLogLevel
from comnetsemu.net import Containernet, VNFManager

B1=10
B2=1
DELAY="10ms"

def myTopology():
    net = Containernet(
    switch=OVSKernelSwitch,
    build=False,
    autoSetMacs=True,
    autoStaticArp=True,
    link=TCLink,
    )
    
    mgr = VNFManager(net)
    setLogLevel("info")

    info("*** Add Switches\n")
    sconfig1 = {"dpid": "%016x" % 1}
    sconfig2 = {"dpid": "%016x" % 2}
    sconfig3 = {"dpid": "%016x" % 3}
    sconfig4 = {"dpid": "%016x" % 4}
    net.addSwitch("s1",**sconfig1)
    net.addSwitch("s2",**sconfig2)
    net.addSwitch("s3",**sconfig3)
    net.addSwitch("s4",**sconfig4)
    info("*** Add Hosts\n")
    host_config = dict(inNamespace=True)
    #net.addHost("h1", **host_config, ip="192.0.0.1")	
    h1 = net.addDockerHost("h1", dimage="dev_test", ip="192.0.0.1", docker_args={"hostname": "h1"},)
    h2 = net.addDockerHost("h2", dimage="dev_test", ip="192.0.0.2", docker_args={"hostname": "h2"},)
    h3 = net.addDockerHost("h3", dimage="dev_test", ip="192.0.0.3", docker_args={"hostname": "h3"},)
    h4 = net.addDockerHost("h4", dimage="dev_test", ip="192.0.0.4", docker_args={"hostname": "h4"},)
    h5 = net.addDockerHost("h5", dimage="dev_test", ip="192.0.0.5", docker_args={"hostname": "h5"},)
    h6 = net.addDockerHost("h6", dimage="dev_test", ip="192.0.0.6", docker_args={"hostname": "h6"},)
    h7 = net.addDockerHost("h7", dimage="dev_test", ip="192.0.0.7", docker_args={"hostname": "h7"},)

    info("*** Add Links\n")
    net.addLink("h1","s1", bw=B1)
    net.addLink("h2","s1", bw=B1)
    net.addLink("h3","s1", bw=B1)
    net.addLink("h4","s1", bw=B1)
    net.addLink("s1","s2", bw=B1)
    net.addLink("s2","s3", bw=B1, delay=DELAY)
    net.addLink("s3","s4", bw=B1, delay=DELAY)
    net.addLink("s2","s4", bw=B2)
    net.addLink("s1","s4", bw=B1)
    net.addLink("s4","h5", bw=B1)
    net.addLink("s4","h6", bw=B1)
    net.addLink("s4","h7", bw=B1)

    info("*** Add controller\n")
    controller = RemoteController("c1", ip="127.0.0.1", port=6633)
    net.addController(controller)
    net.build()
    net.start()
    srv1 = mgr.addContainer("srv1", "h1", "dev_test", "bash", docker_args={},)
    srv2 = mgr.addContainer("srv2", "h2", "echo_server",  "python /home/server.py", docker_args={},)
    srv3 = mgr.addContainer("srv3", "h3", "echo_server",  "python /home/server.py", docker_args={},)
    srv4 = mgr.addContainer("srv4", "h4", "dev_test", "bash", docker_args={},)
    srv5 = mgr.addContainer("srv5", "h5", "dev_test", "bash", docker_args={},)
    srv6 = mgr.addContainer("srv6", "h6", "dev_test", "bash", docker_args={},)
    srv7 = mgr.addContainer("srv7", "h7", "dev_test", "bash", docker_args={},)
    spawnXtermDocker("srv4")
    spawnXtermDocker("srv7")
    CLI(net)
    mgr.removeContainer("srv1")
    mgr.removeContainer("srv2")
    mgr.removeContainer("srv3")
    mgr.removeContainer("srv4")
    mgr.removeContainer("srv5")
    mgr.removeContainer("srv6")
    mgr.removeContainer("srv7")
    net.stop()
    mgr.stop()


if __name__ == "__main__":
    topo = myTopology()