# Estado conhecido do protocolo JOOAN MQTT/DP

O bridge é um inspector dedicado ao `jooanipc`, não um broker MQTT genérico.

## MQTT implementado
- CONNECT / CONNACK
- SUBSCRIBE / SUBACK
- PUBLISH QoS 0/1
- PUBACK
- PINGREQ / PINGRESP
- DISCONNECT
- publicação QoS 0 de comandos para o tópico assinado pela câmera
- TLS opcional

## Tópicos
A família observada começa com `qaiot/mqtt/`. O primeiro tópico assinado nessa família é guardado como `command_topic`.

## DP conhecidos
| cmd | Uso |
| ---: | --- |
| 66485 | salvar preset PTZ |
| 66486 | listar presets PTZ |
| 66489 | atualizar preset |
| 66490 | excluir preset |
| 66491 | ir para preset |
| 66516 | security_enhanced_switch |
| 66517 | security_password |

Exemplo de leitura:
```json
{"cmd":66486,"cmd_type":"request"}
```
