# Redirecionando o jooanipc para o MQTT local

Na JA-A12 analisada pelo projeto ADCDS/jooan-w3u-local-firmware, o endpoint MQTT é:

```text
use1mqtt01.jooaniot.com:443/TCP
```

O guard daquele projeto reescreve esse destino para `127.0.0.2:1883`. Portanto,
1883 é a porta do sink local do retrofit; a conexão OEM original usa TCP 443.

## Opção A — AdGuard direto para o Home Assistant

Com o add-on usando a porta padrão 443:

```text
use1mqtt01.jooaniot.com -> 10.0.0.5
```

A câmera continuará usando o hostname original/SNI, mas abrirá a conexão em:

```text
10.0.0.5:443
```

Não é necessário DNAT para esse método.

## Opção B — AdGuard para o OpenWrt + DNAT

Faça o rewrite:

```text
use1mqtt01.jooaniot.com -> 10.0.0.1
```

Então redirecione somente a câmera:

```text
10.0.0.10 -> 10.0.0.1:443 -> 10.0.0.5:443
```

Use SNAT/hairpin para que a resposta do HA volte obrigatoriamente pelo OpenWrt.

## Importante

Não crie uma regra genérica que intercepte todo TCP/443 originado pela câmera.
O firmware também utiliza outros serviços JOOAN em 443, inclusive
`use1api.jooaniot.com`. O rewrite de DNS deve ser apenas para
`use1mqtt01.jooaniot.com`.

## TLS

O modo `auto` gera uma identidade ECDSA P-256 com CN/SAN
`use1mqtt01.jooaniot.com`. O broker aceita configuração TLS mais antiga quando
`legacy_tls: true`, para aumentar a compatibilidade com o cliente embarcado.

Se a câmera rejeitar o certificado, os logs mostrarão a falha de handshake e a
próxima etapa será reproduzir mais exatamente a identidade TLS usada pelo retrofit.
