FROM ubuntu:latest
LABEL authors="vbaho"

ENTRYPOINT ["top", "-b"]
