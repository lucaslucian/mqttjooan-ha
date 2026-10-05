ARG BUILD_FROM
FROM ${BUILD_FROM}
RUN apk add --no-cache python3 openssl
WORKDIR /opt/mqttjooan
COPY app /opt/mqttjooan/app
COPY run.sh /run.sh
RUN chmod +x /run.sh
EXPOSE 443 8098
CMD ["/run.sh"]
