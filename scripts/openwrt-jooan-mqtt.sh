#!/bin/sh
# mqttjooan-ha - OpenWrt redirect for JOOAN MQTT
#
# Camera:        10.0.0.10
# OpenWrt LAN:   10.0.0.1
# Home Assistant:10.0.0.5
#
# Camera/OEM MQTT destination: TCP 443
# HA published add-on port:    TCP 18883
#
# AdGuard DNS rewrite required for this safe/targeted mode:
# use1mqtt01.jooaniot.com -> 10.0.0.1

set -eu

CAMERA_IP="10.0.0.10"
ROUTER_IP="10.0.0.1"
HA_IP="10.0.0.5"
OEM_PORT="443"
HA_PORT="18883"

delete_named_section() {
    wanted="$1"
    uci show firewall | sed -n "s/^firewall\.\([^.=]*\)\.name='$wanted'$/\1/p" | while read -r section; do
        [ -n "$section" ] && uci -q delete "firewall.$section"
    done
}

# Remove old versions of these rules, including the previous 1883 rules.
delete_named_section "JOOAN-MQTT-Local"
delete_named_section "JOOAN-MQTT-Hairpin"
uci -q delete firewall.jooan_mqtt_local
uci -q delete firewall.jooan_mqtt_hairpin

# DNAT only when the camera is connecting to the ROUTER IP on TCP 443.
# Therefore other TCP/443 destinations used by the camera are left untouched.
uci set firewall.jooan_mqtt_local='redirect'
uci set firewall.jooan_mqtt_local.name='JOOAN-MQTT-Local'
uci set firewall.jooan_mqtt_local.family='ipv4'
uci set firewall.jooan_mqtt_local.src='lan'
uci set firewall.jooan_mqtt_local.src_ip="$CAMERA_IP"
uci set firewall.jooan_mqtt_local.src_dip="$ROUTER_IP"
uci set firewall.jooan_mqtt_local.src_dport="$OEM_PORT"
uci set firewall.jooan_mqtt_local.proto='tcp'
uci set firewall.jooan_mqtt_local.dest='lan'
uci set firewall.jooan_mqtt_local.dest_ip="$HA_IP"
uci set firewall.jooan_mqtt_local.dest_port="$HA_PORT"
uci set firewall.jooan_mqtt_local.target='DNAT'

# Hairpin SNAT: HA sees the source as OpenWrt and replies through OpenWrt.
uci set firewall.jooan_mqtt_hairpin='nat'
uci set firewall.jooan_mqtt_hairpin.name='JOOAN-MQTT-Hairpin'
uci set firewall.jooan_mqtt_hairpin.family='ipv4'
uci set firewall.jooan_mqtt_hairpin.src='lan'
uci set firewall.jooan_mqtt_hairpin.proto='tcp'
uci set firewall.jooan_mqtt_hairpin.src_ip="$CAMERA_IP"
uci set firewall.jooan_mqtt_hairpin.dest_ip="$HA_IP"
uci set firewall.jooan_mqtt_hairpin.dest_port="$HA_PORT"
uci set firewall.jooan_mqtt_hairpin.snat_ip="$ROUTER_IP"
uci set firewall.jooan_mqtt_hairpin.target='SNAT'

uci commit firewall
service firewall restart

echo
echo "=== JOOAN MQTT UCI ==="
uci show firewall | grep -i -A12 -B2 JOOAN || true

echo
echo "=== JOOAN MQTT FW4 ==="
fw4 print | grep -i -A6 -B6 JOOAN || true

echo
echo "Expected flow:"
echo "$CAMERA_IP -> $ROUTER_IP:$OEM_PORT -> $HA_IP:$HA_PORT"
