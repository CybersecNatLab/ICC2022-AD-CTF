FROM mcr.microsoft.com/dotnet/sdk:6.0-alpine3.15 AS builder

WORKDIR /tmp/service
COPY . .

RUN dotnet publish -c Release -o /srv/service



FROM mcr.microsoft.com/dotnet/aspnet:6.0-alpine3.15

RUN apk add --no-cache openssl

COPY --from=builder /srv /srv

RUN mkdir -p /srv/service/data \
 && chown -R nobody: /srv/service 

ENV DOTNET_EnableDiagnostics=0

USER nobody
WORKDIR /srv/service/
CMD dotnet service.dll
