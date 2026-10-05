# mqttjooan-ha

Broker/bridge MQTT local e inspetor de telemetria para câmeras JOOAN que usam o
processo OEM `jooanipc`.

> Estado: **experimental / descoberta de protocolo**. A versão inicial recebe a
> sessão MQTT da câmera, registra todos os PUBLISH e permite enviar DP bruto de
> volta ao tópico assinado pelo `jooanipc`.

## Objetivo

```text
jooanipc
   │
   │ MQTT 3.1.1 / TLS
   ▼
mqttjooan-ha
   ├── captura de telemetria
   ├── visualização de topic/payload/cmd/cmd_type
   ├── envio de DP para o tópico de comando
   └── base para sensores Home Assistant
```

A meta seguinte é mapear os eventos da câmera para entidades do Home Assistant,
principalmente motion, person, vehicle, auto-tracking, floodlight e estados de
gravação.

## O que já funciona

- broker MQTT 3.1.1 mínimo dedicado ao `jooanipc`;
- TLS automático com identidade `use1mqtt01.jooaniot.com`;
- CONNECT, SUBSCRIBE, PUBLISH, QoS 0/1, PING e DISCONNECT;
- captura persistente opcional em `/data/messages.jsonl`;
- detecção de payload JSON, `cmd` e `cmd_type`;
- descoberta automática do tópico de comando `qaiot/mqtt/...`;
- envio de DP bruto pelo painel/API;
- painel web via Home Assistant Ingress;
- estrutura de add-on para Home Assistant;
- execução standalone por Docker Compose para testes.

## Instalação no Home Assistant

Adicione este repositório como repositório de add-ons:

```text
https://github.com/lucaslucian/mqttjooan-ha
```

Instale **MQTT JOOAN HA** e inicie o add-on.

Por padrão a porta interna 1883 é publicada no host como **18883** para não
conflitar com um Mosquitto já existente. Para um DNS rewrite simples, a câmera
precisa conseguir alcançar o bridge na **porta 1883**, então ajuste o mapeamento
de rede do add-on para 1883 ou consulte [docs/REDIRECTION.md](docs/REDIRECTION.md).

## Primeiro teste

O hostname MQTT encontrado no JA-A12 é:

```text
use1mqtt01.jooaniot.com
```

Aponte esse hostname no DNS local para o IP onde o bridge está ouvindo e reinicie
a câmera. Quando houver conexão, o painel deve mostrar:

```text
CONNECT
SUBSCRIBE qaiot/mqtt/...
PUBLISH ...
```

Detalhes e cenários com Mosquitto/porta alternativa:
[docs/REDIRECTION.md](docs/REDIRECTION.md).

## API inicial

```text
GET /api/status
GET /api/messages?limit=100
GET /api/health
POST /api/dp
```

Exemplo de payload para listar presets no JA-A12 analisado:

```json
{
  "payload": {
    "cmd": 66486,
    "cmd_type": "request"
  }
}
```

Não use comandos ainda não identificados em produção. A primeira fase é de
observação e correlação de telemetria.

## Referência técnica

A pesquisa de protocolo e arquitetura se apoia principalmente no excelente
projeto [ADCDS/jooan-w3u-local-firmware](https://github.com/ADCDS/jooan-w3u-local-firmware),
que demonstrou um sink MQTT local para o `jooanipc` da JA-A12. Este repositório
implementa o bridge/inspector de forma independente, focado em descoberta e
integração com Home Assistant.

## Licença

GPL-2.0. Veja `LICENSE`.
