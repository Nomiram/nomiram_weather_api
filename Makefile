grpc:
	python -m grpc_tools.protoc -I. --python_out=./weatherAPI --grpc_python_out=./weatherAPI --pyi_out=./weatherAPI auth.proto
	cd ./weatherAUTH & python -m grpc_tools.protoc -I.. --go_out=./pb --go-grpc_out=./pb auth.proto

build:
	docker-compose build

deploy:
	docker-compose up -d

scale2:
	docker-compose up -d --scale app=2

down:
	docker-compose down

clean:
	docker-compose down --rmi local