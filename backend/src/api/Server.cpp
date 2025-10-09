#include "api/Server.h"
#include <iostream>
#include <sstream>
#include <algorithm>
#include <cctype>
#include <iomanip>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#pragma comment(lib, "ws2_32.lib")
#else
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <fcntl.h>
#endif

namespace api {

SimpleHTTPServer::SimpleHTTPServer(int port) : port_(port) {
#ifdef _WIN32
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);
#endif
}

SimpleHTTPServer::~SimpleHTTPServer() {
    stop();
#ifdef _WIN32
    WSACleanup();
#endif
}

bool SimpleHTTPServer::start() {
    if (running_) {
        return false;
    }
    
    running_ = true;
    server_thread_ = std::thread(&SimpleHTTPServer::serverLoop, this);
    return true;
}

void SimpleHTTPServer::stop() {
    if (running_) {
        running_ = false;
        if (server_thread_.joinable()) {
            server_thread_.join();
        }
    }
}

void SimpleHTTPServer::setRequestHandler(std::function<void(const HTTPRequest&, HTTPResponse&)> handler) {
    std::lock_guard<std::mutex> lock(mutex_);
    request_handler_ = handler;
}

void SimpleHTTPServer::setEventCallback(std::function<void(const std::string&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    event_callback_ = callback;
}

void SimpleHTTPServer::emitEvent(const std::string& event_data) {
    {
        std::lock_guard<std::mutex> lock(event_mutex_);
        events_.push(event_data);
    }
    event_cv_.notify_all();
    
    if (event_callback_) {
        event_callback_(event_data);
    }
}

std::string SimpleHTTPServer::getNextEvent() {
    std::unique_lock<std::mutex> lock(event_mutex_);
    if (events_.empty()) {
        return "";
    }
    
    std::string event = events_.front();
    events_.pop();
    return event;
}

bool SimpleHTTPServer::hasEvents() const {
    std::lock_guard<std::mutex> lock(const_cast<std::mutex&>(event_mutex_));
    return !events_.empty();
}

void SimpleHTTPServer::serverLoop() {
#ifdef _WIN32
    SOCKET server_socket = socket(AF_INET, SOCK_STREAM, 0);
#else
    int server_socket = socket(AF_INET, SOCK_STREAM, 0);
#endif
    
    if (server_socket < 0) {
        std::cerr << "Failed to create socket" << std::endl;
        return;
    }
    
    int opt = 1;
    setsockopt(server_socket, SOL_SOCKET, SO_REUSEADDR, (char*)&opt, sizeof(opt));
    
    sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port_);
    
    if (bind(server_socket, (sockaddr*)&address, sizeof(address)) < 0) {
        std::cerr << "Failed to bind to port " << port_ << std::endl;
#ifdef _WIN32
        closesocket(server_socket);
#else
        close(server_socket);
#endif
        return;
    }
    
    if (listen(server_socket, 10) < 0) {
        std::cerr << "Failed to listen on socket" << std::endl;
#ifdef _WIN32
        closesocket(server_socket);
#else
        close(server_socket);
#endif
        return;
    }
    
    std::cout << "Server listening on port " << port_ << std::endl;
    
    while (running_) {
        sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        
#ifdef _WIN32
        SOCKET client_socket = accept(server_socket, (sockaddr*)&client_addr, &client_len);
#else
        int client_socket = accept(server_socket, (sockaddr*)&client_addr, &client_len);
#endif
        
        if (client_socket >= 0) {
            std::thread client_thread(&SimpleHTTPServer::handleConnection, this, client_socket);
            client_thread.detach();
        }
    }
    
#ifdef _WIN32
    closesocket(server_socket);
#else
    close(server_socket);
#endif
}

void SimpleHTTPServer::handleConnection(int client_socket) {
    char buffer[4096];
    std::string request_data;
    
    int bytes_received = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    if (bytes_received > 0) {
        buffer[bytes_received] = '\0';
        request_data = buffer;
    }
    
    HTTPRequest request = parseRequest(request_data);
    HTTPResponse response;
    
    // Handle SSE endpoint
    if (request.path == "/events/stream") {
        handleSSEConnection(client_socket);
        return;
    }
    
    // Handle regular requests
    if (request_handler_) {
        request_handler_(request, response);
    } else {
        response.status_code = 404;
        response.body = "Not Found";
    }
    
    sendResponse(client_socket, response);
    
#ifdef _WIN32
    closesocket(client_socket);
#else
    close(client_socket);
#endif
}

HTTPRequest SimpleHTTPServer::parseRequest(const std::string& request_data) {
    HTTPRequest request;
    std::istringstream stream(request_data);
    std::string line;
    
    // Parse request line
    if (std::getline(stream, line)) {
        std::istringstream line_stream(line);
        line_stream >> request.method >> request.path;
    }
    
    // Parse headers
    while (std::getline(stream, line) && line != "\r") {
        size_t colon_pos = line.find(':');
        if (colon_pos != std::string::npos) {
            std::string key = line.substr(0, colon_pos);
            std::string value = line.substr(colon_pos + 1);
            
            // Trim whitespace
            key.erase(0, key.find_first_not_of(" \t"));
            key.erase(key.find_last_not_of(" \t\r") + 1);
            value.erase(0, value.find_first_not_of(" \t"));
            value.erase(value.find_last_not_of(" \t\r") + 1);
            
            request.headers[key] = value;
        }
    }
    
    // Parse body
    std::string body_line;
    bool first_line = true;
    while (std::getline(stream, body_line)) {
        if (!first_line) {
            request.body += "\n";
        }
        request.body += body_line;
        first_line = false;
    }
    
    return request;
}

std::string SimpleHTTPServer::buildResponse(const HTTPResponse& response) {
    std::ostringstream oss;
    oss << "HTTP/1.1 " << response.status_code << " ";
    
    switch (response.status_code) {
        case 200: oss << "OK"; break;
        case 404: oss << "Not Found"; break;
        case 500: oss << "Internal Server Error"; break;
        default: oss << "Unknown"; break;
    }
    
    oss << "\r\n";
    
    // Add headers
    for (const auto& header : response.headers) {
        oss << header.first << ": " << header.second << "\r\n";
    }
    
    oss << "Content-Length: " << response.body.length() << "\r\n";
    oss << "\r\n";
    oss << response.body;
    
    return oss.str();
}

void SimpleHTTPServer::sendResponse(int client_socket, const HTTPResponse& response) {
    std::string response_str = buildResponse(response);
    send(client_socket, response_str.c_str(), response_str.length(), 0);
}

void SimpleHTTPServer::handleSSEConnection(int client_socket) {
    // Send SSE headers
    std::string sse_headers = 
        "HTTP/1.1 200 OK\r\n"
        "Content-Type: text/event-stream\r\n"
        "Cache-Control: no-cache\r\n"
        "Connection: keep-alive\r\n"
        "Access-Control-Allow-Origin: *\r\n"
        "\r\n";
    
    send(client_socket, sse_headers.c_str(), sse_headers.length(), 0);
    
    // Send events
    while (running_) {
        std::unique_lock<std::mutex> lock(event_mutex_);
        event_cv_.wait(lock, [this] { return !events_.empty() || !running_; });
        
        if (!running_) break;
        
        while (!events_.empty()) {
            std::string event = events_.front();
            events_.pop();
            
            std::string sse_event = "data: " + event + "\n\n";
            send(client_socket, sse_event.c_str(), sse_event.length(), 0);
        }
    }
}

std::string SimpleHTTPServer::urlDecode(const std::string& str) const {
    std::string result;
    for (size_t i = 0; i < str.length(); ++i) {
        if (str[i] == '%' && i + 2 < str.length()) {
            int hex = std::stoi(str.substr(i + 1, 2), nullptr, 16);
            result += static_cast<char>(hex);
            i += 2;
        } else if (str[i] == '+') {
            result += ' ';
        } else {
            result += str[i];
        }
    }
    return result;
}

std::string SimpleHTTPServer::urlEncode(const std::string& str) const {
    std::ostringstream escaped;
    escaped.fill('0');
    escaped << std::hex;
    
    for (char c : str) {
        if (std::isalnum(c) || c == '-' || c == '_' || c == '.' || c == '~') {
            escaped << c;
        } else {
            escaped << '%' << std::setw(2) << static_cast<int>(static_cast<unsigned char>(c));
        }
    }
    
    return escaped.str();
}

std::map<std::string, std::string> SimpleHTTPServer::parseQueryParams(const std::string& query) const {
    std::map<std::string, std::string> params;
    std::istringstream stream(query);
    std::string pair;
    
    while (std::getline(stream, pair, '&')) {
        size_t eq_pos = pair.find('=');
        if (eq_pos != std::string::npos) {
            std::string key = urlDecode(pair.substr(0, eq_pos));
            std::string value = urlDecode(pair.substr(eq_pos + 1));
            params[key] = value;
        }
    }
    
    return params;
}

std::string SimpleHTTPServer::toJSON(const std::map<std::string, std::string>& data) const {
    JSONBuilder json;
    json.startObject();
    
    bool first = true;
    for (const auto& pair : data) {
        if (!first) json.addComma();
        json.addKey(pair.first).addString(pair.second);
        first = false;
    }
    
    json.endObject();
    return json.build();
}

// JSONBuilder implementation
JSONBuilder& JSONBuilder::startObject() {
    json_ << "{";
    return *this;
}

JSONBuilder& JSONBuilder::endObject() {
    json_ << "}";
    return *this;
}

JSONBuilder& JSONBuilder::startArray() {
    json_ << "[";
    return *this;
}

JSONBuilder& JSONBuilder::endArray() {
    json_ << "]";
    return *this;
}

JSONBuilder& JSONBuilder::addKey(const std::string& key) {
    json_ << "\"" << key << "\":";
    return *this;
}

JSONBuilder& JSONBuilder::addString(const std::string& value) {
    json_ << "\"" << value << "\"";
    return *this;
}

JSONBuilder& JSONBuilder::addNumber(double value) {
    json_ << value;
    return *this;
}

JSONBuilder& JSONBuilder::addBoolean(bool value) {
    json_ << (value ? "true" : "false");
    return *this;
}

JSONBuilder& JSONBuilder::addNull() {
    json_ << "null";
    return *this;
}

JSONBuilder& JSONBuilder::addComma() {
    json_ << ",";
    return *this;
}

std::string JSONBuilder::build() {
    return json_.str();
}

} // namespace api
