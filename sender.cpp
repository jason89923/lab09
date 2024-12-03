#include <iostream>
#include <wiringPi.h>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <chrono>
#include <stdio.h>

using namespace std;
using namespace std::chrono;

const int led = 1;     // GPIO1
const int onoff = 4;   // GPIO4
const char *receiverIP = "127.0.0.1"; // 接收端的 IP 地址
const int receiverPort = 8080;        // 接收端的 Port

int sock = 0;

void setupSocket() {
    struct sockaddr_in serv_addr;
    sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock < 0) {
        cerr << "Socket creation error\n";
        exit(1);
    }

    serv_addr.sin_family = AF_INET;
    serv_addr.sin_port = htons(receiverPort);

    // 轉換 IP 地址格式
    if (inet_pton(AF_INET, receiverIP, &serv_addr.sin_addr) <= 0) {
        cerr << "Invalid address/ Address not supported \n";
        exit(1);
    }

    if (connect(sock, (struct sockaddr *)&serv_addr, sizeof(serv_addr)) < 0) {
        cerr << "Connection Failed\n";
        exit(1);
    }
}

void sendButtonState(int state) {
    char buffer[2];
    buffer[0] = state ? '1' : '0';
    buffer[1] = '\0';
    send(sock, buffer, sizeof(buffer), 0);
}

int main() {
    if (wiringPiSetup() == -1) {
        cerr << "Failed to setup WiringPi.\n";
        return 0;
    }

    pinMode(led, OUTPUT);
    pinMode(onoff, INPUT);

    setupSocket(); // 初始化 Socket 連接

    int prevState = -1;
    steady_clock::time_point pressTime, releaseTime;

    while (1) {
        int currentState = digitalRead(onoff);

        if (currentState != prevState) {
            if (currentState == 1) {
                digitalWrite(led, 1);   // LED 亮
                sendButtonState(1);     // 傳送按下狀態
            } else {
                digitalWrite(led, 0);   // LED 滅
                sendButtonState(0);     // 傳送放開狀態
            }
            prevState = currentState;
        }
        delay(50);
    }

    close(sock); // 關閉 Socket 連接
    return 0;
}