package main

import (
	"bufio"
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net"
	"os"
	"weatherAUTH/pb"

	"google.golang.org/grpc"
)

type GRPCServer struct {
	pb.AuthServiceServer
}
type User struct {
	User bool `json:"user"`
	Flag bool `json:"flag"`
}

var usernames = loadConfig("users.json")

func loadConfig(name string) map[string]bool {
	file, err := os.Open(name)
	if err != nil {
		log.Fatal(err)
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	var jsonStr string
	for scanner.Scan() {
		jsonStr += scanner.Text()
	}

	var user map[string]bool
	err = json.Unmarshal([]byte(jsonStr), &user)
	if err != nil {
		log.Fatal(err)
	}
	return user
}

func (G GRPCServer) CheckAuthorization(ctx context.Context, request *pb.AuthRequest) (*pb.AuthResponse, error) {

	checkResult := false
	if _, ok := usernames[request.Username]; ok {
		checkResult = true
	}
	return &pb.AuthResponse{Check: checkResult}, nil
}

func main() {
	s := grpc.NewServer()
	srv := &GRPCServer{}
	pb.RegisterAuthServiceServer(s, srv)
	port, ok := os.LookupEnv("GRPC_PORT")
	if !ok {
		port = ":50051"
	}
	l, err := net.Listen("tcp", ":"+port)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Сервер запущен")

	if err := s.Serve(l); err != nil {
		log.Fatal(err)
	}
}
