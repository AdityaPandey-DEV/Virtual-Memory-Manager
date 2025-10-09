#pragma once

#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <queue>
#include <condition_variable>
#include <functional>
#include <memory>
#include <map>
#include <sstream>

namespace api {

struct HTTPRequest {
    std::string method;
    std::string path;
    std::map<std::string, std::string> headers;
    std::string body;
    
    HTTPRequest() = default;
    HTTPRequest(const std::string& m, const std::string& p, const std::string& b = "")
        : method(m), path(p), body(b) {}
};

struct HTTPResponse {
    int status_code = 200;
    std::map<std::string, std::string> headers;
    std::string body;
    
    HTTPResponse() = default;
    HTTPResponse(int code, const std::string& b) : status_code(code), body(b) {}
};

class SimpleHTTPServer {
private:
    int port_;
    std::atomic<bool> running_{false};
    std::thread server_thread_;
    std::mutex mutex_;
    
    // Event streaming
    std::queue<std::string> events_;
    std::condition_variable event_cv_;
    std::mutex event_mutex_;
    
    // Callbacks
    std::function<void(const HTTPRequest&, HTTPResponse&)> request_handler_;
    std::function<void(const std::string&)> event_callback_;

public:
    explicit SimpleHTTPServer(int port = 8080);
    ~SimpleHTTPServer();
    
    // Server control
    bool start();
    void stop();
    bool isRunning() const { return running_; }
    
    // Request handling
    void setRequestHandler(std::function<void(const HTTPRequest&, HTTPResponse&)> handler);
    
    // Event streaming
    void setEventCallback(std::function<void(const std::string&)> callback);
    void emitEvent(const std::string& event_data);
    std::string getNextEvent();
    bool hasEvents() const;
    
    // Utility
    std::string urlDecode(const std::string& str) const;
    std::string urlEncode(const std::string& str) const;
    std::map<std::string, std::string> parseQueryParams(const std::string& query) const;
    std::string toJSON(const std::map<std::string, std::string>& data) const;

private:
    void serverLoop();
    void handleConnection(int client_socket);
    HTTPRequest parseRequest(const std::string& request_data);
    std::string buildResponse(const HTTPResponse& response);
    void sendResponse(int client_socket, const HTTPResponse& response);
    void handleSSEConnection(int client_socket);
};

// JSON utilities
class JSONBuilder {
private:
    std::ostringstream json_;

public:
    JSONBuilder& startObject();
    JSONBuilder& endObject();
    JSONBuilder& startArray();
    JSONBuilder& endArray();
    JSONBuilder& addKey(const std::string& key);
    JSONBuilder& addString(const std::string& value);
    JSONBuilder& addNumber(double value);
    JSONBuilder& addBoolean(bool value);
    JSONBuilder& addNull();
    JSONBuilder& addComma();
    std::string build();
};

} // namespace api
