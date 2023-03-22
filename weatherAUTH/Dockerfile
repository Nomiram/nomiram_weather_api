FROM golang:1.20 as build

WORKDIR /app
COPY ./go.mod ./go.sum ./
RUN ["go", "mod", "download"]
COPY . .
ENV CGO_ENABLED=0
RUN ["go", "build", "-o", "authserver", "./main.go"]

FROM alpine
COPY --from=build /app/authserver /
COPY --from=build /app/users.json /
CMD ["/authserver"]
