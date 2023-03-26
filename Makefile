build:
	docker-compose build
grpc:
	python -m grpc_tools.protoc -I. --python_out=./weatherAPI --grpc_python_out=./weatherAPI --pyi_out=./weatherAPI auth.proto
	cd ./weatherAUTH & python -m grpc_tools.protoc -I.. --go_out=./pb --go-grpc_out=./pb auth.proto
# usage: make deploy scale=2
ifndef scale
deploy:
	docker-compose up -d
else
deploy:
	docker-compose up -d --scale app=$(scale) --scale auth=$(scale)
endif
down:
	docker-compose down
clean:
	docker-compose down --rmi local