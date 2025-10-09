#include <iostream>
#include <thread>
#include <chrono>
#include <memory>
#include <signal.h>
#include <algorithm>
#include <atomic>

#include "vmm/VMM.h"
#include "workload/WorkloadGen.h"
#include "api/Server.h"

using namespace vmm;
using namespace workload;
using namespace api;

class VMMSimulator {
private:
    std::unique_ptr<VMM> vmm_;
    std::unique_ptr<WorkloadGenerator> workload_gen_;
    std::unique_ptr<SimpleHTTPServer> server_;
    
    std::thread simulation_thread_;
    std::atomic<bool> simulation_running_{false};
    std::atomic<bool> server_running_{false};
    
    VMMConfig vmm_config_;
    WorkloadConfig workload_config_;

public:
    VMMSimulator() {
        // Initialize VMM with default config
        vmm_config_.total_frames = 256;
        vmm_config_.page_size = 4096;
        vmm_config_.total_pages = 1024;
        vmm_config_.replacement_policy = ReplacementPolicy::CLOCK;
        vmm_config_.enable_ai_predictions = true;
        vmm_config_.ai_predictor_url = "http://localhost:5001/predict";
        
        // Initialize workload with default config
        workload_config_.type = WorkloadType::RANDOM;
        workload_config_.total_requests = 1000;
        workload_config_.page_range = 1000;
        workload_config_.stride = 1;
        workload_config_.zipf_alpha = 1.0;
        workload_config_.locality_factor = 0.8;
        workload_config_.working_set_size = 100;
        
        vmm_ = std::make_unique<VMM>(vmm_config_);
        workload_gen_ = std::make_unique<WorkloadGenerator>(workload_config_);
        server_ = std::make_unique<SimpleHTTPServer>(8080);
        
        setupEventHandlers();
        setupAPIHandlers();
    }
    
    ~VMMSimulator() {
        stopSimulation();
        if (server_running_) {
            server_->stop();
        }
    }
    
    void start() {
        std::cout << "Starting VMM Simulator..." << std::endl;
        
        // Start HTTP server
        if (server_->start()) {
            server_running_ = true;
            std::cout << "HTTP server started on port 8080" << std::endl;
        } else {
            std::cerr << "Failed to start HTTP server" << std::endl;
            return;
        }
        
        // Start VMM simulation
        vmm_->startSimulation();
        std::cout << "VMM simulation started" << std::endl;
    }
    
    void stop() {
        stopSimulation();
        if (server_running_) {
            server_->stop();
            server_running_ = false;
        }
    }

private:
    void setupEventHandlers() {
        // VMM event handler
        vmm_->setEventCallback([this](const VMMEvent& event) {
            std::string event_json = buildEventJSON(event);
            server_->emitEvent(event_json);
        });
        
        // Workload access handler
        workload_gen_->setAccessCallback([this](int page, bool is_write) {
            vmm_->accessPage(page, is_write);
        });
        
        // Workload completion handler
        workload_gen_->setCompletionCallback([this]() {
            std::cout << "Workload completed, restarting..." << std::endl;
            // Reset and restart the workload instead of stopping
            workload_gen_->reset();
            workload_gen_->start();
        });
    }
    
    void setupAPIHandlers() {
        server_->setRequestHandler([this](const HTTPRequest& request, HTTPResponse& response) {
            handleAPIRequest(request, response);
        });
    }
    
    void handleAPIRequest(const HTTPRequest& request, HTTPResponse& response) {
        response.headers["Content-Type"] = "application/json";
        response.headers["Access-Control-Allow-Origin"] = "*";
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS";
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization";
        
        // Handle CORS preflight requests
        if (request.method == "OPTIONS") {
            response.status_code = 200;
            response.body = "";
            return;
        }
        
        if (request.method == "GET" && request.path == "/metrics") {
            handleGetMetrics(response);
        }
        else if (request.method == "POST" && request.path == "/simulate/start") {
            handleStartSimulation(request, response);
        }
        else if (request.method == "POST" && request.path == "/simulate/stop") {
            handleStopSimulation(response);
        }
        else if (request.method == "GET" && request.path == "/events/stream") {
            // SSE handled separately
            response.status_code = 200;
        }
        else {
            response.status_code = 404;
            response.body = "{\"error\": \"Not Found\"}";
        }
    }
    
    void handleGetMetrics(HTTPResponse& response) {
        JSONBuilder json;
        json.startObject()
            .addKey("total_accesses").addNumber(static_cast<double>(vmm_->getTotalAccesses()))
            .addComma()
            .addKey("page_faults").addNumber(static_cast<double>(vmm_->getPageFaults()))
            .addComma()
            .addKey("page_fault_rate").addNumber(vmm_->getPageFaultRate())
            .addComma()
            .addKey("swap_ins").addNumber(static_cast<double>(vmm_->getSwapIns()))
            .addComma()
            .addKey("swap_outs").addNumber(static_cast<double>(vmm_->getSwapOuts()))
            .addComma()
            .addKey("ai_predictions").addNumber(static_cast<double>(vmm_->getAIPredictions()))
            .addComma()
            .addKey("ai_hit_rate").addNumber(vmm_->getAIHitRate())
            .addComma()
            .addKey("ai_prediction_confidence").addNumber(vmm_->getAIPredictionConfidence())
            .addComma()
            .addKey("free_frames").addNumber(static_cast<double>(vmm_->getFreeFrameCount()))
            .addComma()
            .addKey("used_frames").addNumber(static_cast<double>(vmm_->getUsedFrameCount()))
            .endObject();
        
        response.body = json.build();
    }
    
    void handleStartSimulation(const HTTPRequest& request, HTTPResponse& response) {
        // Parse request body for workload configuration
        std::string mode = "prefetch_only";
        std::string workload = "random";
        
        std::cout << "Raw request body length: " << request.body.length() << std::endl;
        std::cout << "Raw request body: '" << request.body << "'" << std::endl;
        
        if (!request.body.empty()) {
            // Remove newlines and carriage returns from body for cleaner JSON parsing
            std::string clean_body = request.body;
            clean_body.erase(std::remove(clean_body.begin(), clean_body.end(), '\n'), clean_body.end());
            clean_body.erase(std::remove(clean_body.begin(), clean_body.end(), '\r'), clean_body.end());
            
            std::cout << "Clean request body: '" << clean_body << "'" << std::endl;
            
            // Look for mode in JSON - handle both quoted and unquoted values
            size_t mode_pos = clean_body.find("\"mode\":");
            if (mode_pos != std::string::npos) {
                mode_pos += 7; // Skip "mode":
                // Skip whitespace
                while (mode_pos < clean_body.length() && (clean_body[mode_pos] == ' ' || clean_body[mode_pos] == '\t')) {
                    mode_pos++;
                }
                // Check if value is quoted
                if (mode_pos < clean_body.length() && clean_body[mode_pos] == '"') {
                    mode_pos++; // Skip opening quote
                    size_t mode_end = clean_body.find("\"", mode_pos);
                    if (mode_end != std::string::npos) {
                        mode = clean_body.substr(mode_pos, mode_end - mode_pos);
                        std::cout << "Parsed mode: " << mode << std::endl;
                    }
                }
            }
            
            // Look for workload in JSON - handle both quoted and unquoted values
            size_t workload_pos = clean_body.find("\"workload\":");
            if (workload_pos != std::string::npos) {
                workload_pos += 11; // Skip "workload":
                // Skip whitespace
                while (workload_pos < clean_body.length() && (clean_body[workload_pos] == ' ' || clean_body[workload_pos] == '\t')) {
                    workload_pos++;
                }
                // Check if value is quoted
                if (workload_pos < clean_body.length() && clean_body[workload_pos] == '"') {
                    workload_pos++; // Skip opening quote
                    size_t workload_end = clean_body.find("\"", workload_pos);
                    if (workload_end != std::string::npos) {
                        workload = clean_body.substr(workload_pos, workload_end - workload_pos);
                        std::cout << "Parsed workload: " << workload << std::endl;
                    }
                }
            }
        }
        
        std::cout << "Final parsed values - mode: " << mode << ", workload: " << workload << std::endl;
        
        // Update VMM configuration based on mode
        if (mode == "ai_off") {
            vmm_config_.enable_ai_predictions = false;
            std::cout << "AI predictions disabled" << std::endl;
        } else {
            vmm_config_.enable_ai_predictions = true;
            std::cout << "AI predictions enabled" << std::endl;
        }
        
        // Update workload configuration
        if (workload == "sequential") {
            workload_config_.type = WorkloadType::SEQUENTIAL;
            std::cout << "Workload type set to SEQUENTIAL" << std::endl;
        } else if (workload == "strided") {
            workload_config_.type = WorkloadType::STRIDED;
            std::cout << "Workload type set to STRIDED" << std::endl;
        } else if (workload == "db_like") {
            workload_config_.type = WorkloadType::ZIPF;
            std::cout << "Workload type set to ZIPF (DB-like)" << std::endl;
        } else {
            workload_config_.type = WorkloadType::RANDOM;
            std::cout << "Workload type set to RANDOM" << std::endl;
        }
        
        // Apply configuration changes
        vmm_->setConfig(vmm_config_);
        workload_gen_->setConfig(workload_config_);
        
        std::cout << "Configuration applied successfully" << std::endl;
        
        startSimulation();
        
        response.status_code = 200;
        JSONBuilder json;
        json.startObject()
            .addKey("status").addString("started")
            .addComma()
            .addKey("workload_type").addString(workload)
            .addComma()
            .addKey("ai_mode").addString(mode)
            .endObject();
        
        response.body = json.build();
    }
    
    void handleStopSimulation(HTTPResponse& response) {
        stopSimulation();
        
        response.status_code = 200;
        JSONBuilder json;
        json.startObject()
            .addKey("status").addString("stopped")
            .endObject();
        
        response.body = json.build();
    }
    
    void startSimulation() {
        if (!simulation_running_) {
            simulation_running_ = true;
            workload_gen_->start();
            
            simulation_thread_ = std::thread([this]() {
                while (simulation_running_ && workload_gen_->isRunning()) {
                    workload_gen_->generateNextAccess();
                    std::this_thread::sleep_for(std::chrono::milliseconds(10));
                }
            });
        }
    }
    
    void stopSimulation() {
        if (simulation_running_) {
            simulation_running_ = false;
            workload_gen_->stop();
            vmm_->stopSimulation();
            
            if (simulation_thread_.joinable()) {
                simulation_thread_.join();
            }
        }
    }
    
    std::string buildEventJSON(const VMMEvent& event) {
        JSONBuilder json;
        json.startObject()
            .addKey("type").addString(event.type)
            .addComma()
            .addKey("message").addString(event.message)
            .addComma()
            .addKey("timestamp").addNumber(event.timestamp);
        
        if (!event.data.empty()) {
            json.addComma().addKey("data").addString(event.data);
        }
        
        json.endObject();
        return json.build();
    }
};

// Global simulator instance for signal handling
std::unique_ptr<VMMSimulator> g_simulator;

void signalHandler(int signal) {
    std::cout << "\nReceived signal " << signal << ", shutting down..." << std::endl;
    if (g_simulator) {
        g_simulator->stop();
    }
    exit(0);
}

int main() {
    std::cout << "Virtual Memory Manager Simulator" << std::endl;
    std::cout << "=================================" << std::endl;
    
    // Setup signal handlers
    signal(SIGINT, signalHandler);
    signal(SIGTERM, signalHandler);
    
    try {
        g_simulator = std::make_unique<VMMSimulator>();
        g_simulator->start();
        
        std::cout << "\nServer is running. Press Ctrl+C to stop." << std::endl;
        std::cout << "Available endpoints:" << std::endl;
        std::cout << "  GET  /metrics - Get simulation metrics" << std::endl;
        std::cout << "  POST /simulate/start - Start simulation" << std::endl;
        std::cout << "  POST /simulate/stop - Stop simulation" << std::endl;
        std::cout << "  GET  /events/stream - Stream events (SSE)" << std::endl;
        
        // Keep main thread alive
        while (true) {
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
