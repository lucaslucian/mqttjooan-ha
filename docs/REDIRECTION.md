# Redirecionando o jooanipc para o MQTT local

No JA-A12 usado como referência, o endpoint MQTT OEM é:

```text
use1mqtt01.jooaniot.com:443/TCP
```

O `mqttjooan-ha` continua ouvindo **internamente em TCP 443**, mas o add-on
publica essa porta no host do Home Assistant como **TCP 18883** para não
conflitar com HTTPS/443 existente.

## Layout recomendado

```text
JOOAN 10.0.0.10
        |
        | DNS: use1mqtt01.jooaniot.com -> 10.0.0.1
        |
        v
OpenWrt 10.0.0.1:443
        |
        | DNAT 443 -> 18883
        | SNAT/hairpin
        v
Home Assistant 10.0.0.5:18883
        |
        | add-on port mapping
        v
mqttjooan-ha container :443
```

## AdGuard

Crie somente:

```text
use1mqtt01.jooaniot.com -> 10.0.0.1
```

Não aponte diretamente para `10.0.0.5` neste layout, porque a câmera conecta
em TCP 443 e o add-on está publicado no host em 18883.

Não reescreva `use1api.jooaniot.com`.

## OpenWrt

O script pronto está em:

```text
scripts/openwrt-jooan-mqtt.sh
```

Ele cria uma regra restrita:

```text
origem:  10.0.0.10
destino original: 10.0.0.1:443
DNAT:    10.0.0.5:18883
SNAT:    10.0.0.1
```

Como a regra exige `destino original = 10.0.0.1`, ela não captura as demais
conexões HTTPS da câmera para outros serviços.

## TLS

O TLS atravessa o OpenWrt sem ser terminado ou alterado. O add-on termina a
sessão TLS e apresenta certificado ECDSA P-256 com CN/SAN
`use1mqtt01.jooaniot.com`.

Se a câmera rejeitar o certificado, o log do add-on mostrará a falha de
handshake para continuarmos a compatibilização.
