# mqttjooan-ha

Broker/bridge MQTT local e inspetor de telemetria para câmeras JOOAN que usam o
processo OEM `jooanipc`.

> Estado: **experimental / descoberta de protocolo**. A versão inicial recebe a
> sessão MQTT da câmera, registra todos os PUBLISH e permite enviar DP bruto de
> volta ao tópico assinado pelo `jooanipc`.

## Porta/protocolo confirmados

No JA-A12 usado como referência, o `jooanipc` conecta ao endpoint MQTT OEM:

```text
use1mqtt01.jooaniot.com:443/TCP
```

com TLS. O projeto ADCDS redireciona essa conexão internamente para
`127.0.0.2:1883`; portanto, **1883 é a porta do sink local do retrofit, não a
porta original do serviço JOOAN**.

A partir da v0.1.2, o broker continua em **TCP 443 dentro do container**, mas o Home Assistant publica o add-on em **TCP 18883** para evitar conflito com HTTPS.

## Objetivo

```text
jooanipc
   │
   │ MQTT 3.1.1 / TLS / TCP 443
   ▼
mqttjooan-ha
   ├── captura de telemetria
   ├── visualização de topic/payload/cmd/cmd_type
   ├── envio de DP para o tópico de comando
   └── base para sensores Home Assistant
```

## O que já funciona

- broker MQTT 3.1.1 mínimo dedicado ao `jooanipc`;
- TLS automático com identidade ECDSA para `use1mqtt01.jooaniot.com`;
- CONNECT, SUBSCRIBE, PUBLISH, QoS 0/1, PING e DISCONNECT;
- captura persistente opcional em `/data/messages.jsonl`;
- detecção de payload JSON, `cmd` e `cmd_type`;
- descoberta automática do tópico de comando `qaiot/mqtt/...`;
- envio de DP bruto pelo painel/API;
- painel web via Home Assistant Ingress.

## Instalação no Home Assistant

Adicione:

```text
https://github.com/lucaslucian/mqttjooan-ha
```

à loja de add-ons e instale **MQTT JOOAN HA**.

A porta padrão é:

```text
443/tcp -> 443
```

Se a porta 443 já estiver ocupada no host do Home Assistant, mude a porta
publicada e use o redirecionamento OpenWrt documentado em
[docs/REDIRECTION.md](docs/REDIRECTION.md).

## Primeiro teste recomendado

Para teste direto por DNS:

```text
use1mqtt01.jooaniot.com -> 10.0.0.5
```

Reinicie a câmera. O painel deverá começar a mostrar CONNECT, SUBSCRIBE e
PUBLISH caso o handshake TLS seja aceito.

## API inicial

```text
GET /api/status
GET /api/messages?limit=100
GET /api/health
POST /api/dp
```

## Referência técnica

A pesquisa se apoia principalmente em
[ADCDS/jooan-w3u-local-firmware](https://github.com/ADCDS/jooan-w3u-local-firmware).
O vetor `redirect-approved-mqtt` desse projeto documenta a conexão OEM MQTT
original em TCP 443 e sua reescrita local para TCP 1883.

## Licença

GPL-2.0.
