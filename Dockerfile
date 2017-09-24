FROM python:3.5-slim

COPY ./ /tmp

WORKDIR /tmp

RUN ls -la /tmp
RUN chmod +x ./build/docker-entrypoint.sh
RUN pip3 install -r ./requirements.txt

EXPOSE 8000

ENTRYPOINT ["./build/docker-entrypoint.sh"]
