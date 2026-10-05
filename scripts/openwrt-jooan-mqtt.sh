#!/bin/sh
# mqttjooan-ha - OpenWrt redirect for JOOAN MQTT
# Camera: 10.0.0.10
# OpenWrt LAN: 10.0.0.1
# Home Assistant: 10.0.0.5
# Expected OEM MQTT endpoint: use1mqtt01.jooaniot.com:443/TCP
#
# Use together with an AdGuard DNS rewrite:
# use1mqtt01.jooaniot.com -> 10.0.0.1

set -eu

CAMERA_IP="10.0.0.10"
ROUTER_IP="10.0.0.1"
HA_IP="10.0.0.5"
MQTT_PORT="443"

delete_named_section() {
    wanted="$1"
    uci show firewall | sed -n "s/^firewall\.\([^.=]*\)\.name='$wanted'$/\1/p" | while read -r section; do
        [ -n "$section" ] && uci -q delete "firewall.$section"
    done
}

delete_named_section "JOOAN-MQTT-Local"
delete_named_section "JOOAN-MQTT-Hairpin"

uci -q delete firewall.jooan_mqtt_local
uci -q delete firewall.jooan_mqtt_hairpin

# Only traffic from the camera to the router's own TCP/443 is redirected.
# This avoids hijacking other HTTPS/JOOAN API connections from the camera.
uci set firewall.jooan_mqtt_local='redirect'
uci set firewall.jooan_mqtt_local.name='JOOAN-MQTT-Local'
uci set firewall.jooan_mqtt_local.family='ipv4'
uci set firewall.jooan_mqtt_local.src='lan'
uci set firewall.jooan_mqtt_local.src_ip="$CAMERA_IP"
uci set firewall.jooan_mqtt_local.src_dip="$ROUTER_IP"
uci set firewall.jooan_mqtt_local.proto='tcp'
uci set firewall.jooan_mqtt_local.src_dport="$MQTT_PORT"
uci set firewall.jooan_mqtt_local.dest='lan'
uci set firewall.jooan_mqtt_local.dest_ip="$HA_IP"
uci set firewall.jooan_mqtt_local.dest_port="$MQTT_PORT"
uci set firewall.jooan_mqtt_local.target='DNAT'

# Force the reply path through OpenWrt (LAN -> LAN hairpin).
uci set firewall.jooan_mqtt_hairpin='nat'
uci set firewall.jooan_mqtt_hairpin.name='JOOAN-MQTT-Hairpin'
uci set firewall.jooan_mqtt_hairpin.family='ipv4'
uci set firewall.jooan_mqtt_hairpin.src='lan'
uci set firewall.jooan_mqtt_hairpin.proto='tcp'
uci set firewall.jooan_mqtt_hairpin.src_ip="$CAMERA_IP"
uci set firewall.jooan_mqtt_hairpin.dest_ip="$HA_IP"
uci set firewall.jooan_mqtt_hairpin.dest_port="$MQTT_PORT"
uci set firewall.jooan_mqtt_hairpin.snat_ip="$ROUTER_IP"
uci set firewall.jooan_mqtt_hairpin.target='SNAT'

uci commit firewall
service firewall restart

echo
echo "JOOAN MQTT rules:"
uci show firewall | grep -i -A12 -B2 JOOAN || true
echo
echo "Compiled fw4 rules:"
fw4 print | grep -i -A6 -B6 JOOAN || true
