# Changelog

## 0.1.2
- keep the broker listening internally on OEM TCP 443;
- expose the Home Assistant host port as TCP 18883 to avoid conflicts with HA/HTTPS;
- update OpenWrt DNAT/hairpin examples for 443 -> 18883;
- clarify that AdGuard should rewrite the MQTT hostname to the OpenWrt LAN IP in this layout.

## 0.1.1
- corrected the OEM cloud MQTT destination to TCP 443;
- add-on now listens internally on TCP 443;
- automatic certificate changed to ECDSA P-256;
- legacy TLS option is now applied by the broker;
- improved TLS handshake logging;
- redirection documentation updated for AdGuard/OpenWrt.

## 0.1.0
- initial local MQTT 3.1.1 broker;
- automatic/custom/off TLS;
- CONNECT/SUBSCRIBE/PUBLISH capture;
- QoS 0/1;
- web inspector via HA Ingress;
- JSONL persistence;
- raw DP sending to the camera subscription topic.
