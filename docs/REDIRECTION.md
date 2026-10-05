# Redirecionando o jooanipc para o MQTT local

Na unidade JA-A12 analisada pelo projeto ADCDS/jooan-w3u-local-firmware, o `jooanipc` resolve:

```text
use1mqtt01.jooaniot.com
```

## Teste recomendado
1. Faça o bridge ficar acessível em TCP **1883**.
2. No DNS local, crie:
```text
use1mqtt01.jooaniot.com -> IP_DO_MQTTJOOAN
```
3. Reinicie a câmera.
4. No painel do add-on devem aparecer CONNECT, SUBSCRIBE e PUBLISH.

## Se a 1883 já estiver ocupada pelo Mosquitto
O add-on usa 18883 no host por padrão. DNS não troca porta, então escolha uma das opções:
- alterar o mapeamento do add-on para host 1883 temporariamente;
- executar o bridge em outro IP onde a 1883 esteja livre;
- aplicar DNAT, somente para o IP da câmera, de destino TCP/1883 para IP_DO_MQTTJOOAN:18883.

## TLS
O modo `auto` gera certificado com CN/SAN `use1mqtt01.jooaniot.com`. Isso funciona se o cliente OEM não exigir uma CA específica. Se o handshake falhar, primeiro confirme o tráfego e então teste `tls_mode: off` apenas como diagnóstico.

## Método comprovado no retrofit JA-A12
O projeto ADCDS usa LD_PRELOAD dentro da própria câmera para redirecionar:
```text
use1mqtt01.jooaniot.com -> 127.0.0.2
```
Não aplique esse shim binário a outro firmware sem validar o hash/ABI do `jooanipc`.
