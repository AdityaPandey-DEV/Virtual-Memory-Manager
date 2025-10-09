#pragma once

#include "PageTable.h"
#include "Replacement.h"
#include <vector>
#include <memory>
#include <atomic>
#include <mutex>
#include <functional>
#include <string>
#include <chrono>

namespace vmm {

struct VMMConfig {
    size_t total_frames = 256;
    size_t page_size = 4096;
    size_t total_pages = 1024;
    ReplacementPolicy replacement_policy = ReplacementPolicy::CLOCK;
    bool enable_ai_predictions = false;
    std::string ai_predictor_url = "http://localhost:5000/predict";
};

struct VMMMetrics {
    std::atomic<size_t> total_accesses{0};
    std::atomic<size_t> page_faults{0};
    std::atomic<size_t> swap_ins{0};
    std::atomic<size_t> swap_outs{0};
    std::atomic<size_t> ai_predictions{0};
    std::atomic<size_t> ai_hits{0};
    
    // Delete copy constructor and assignment operator
    VMMMetrics() = default;
    VMMMetrics(const VMMMetrics&) = delete;
    VMMMetrics& operator=(const VMMMetrics&) = delete;
    
    double getPageFaultRate() const {
        return total_accesses > 0 ? static_cast<double>(page_faults) / total_accesses : 0.0;
    }
    
    double getAIHitRate() const {
        return ai_predictions > 0 ? static_cast<double>(ai_hits) / ai_predictions : 0.0;
    }
};

struct VMMEvent {
    std::string type;
    std::string message;
    size_t timestamp;
    std::string data;
    
    VMMEvent(const std::string& t, const std::string& msg, const std::string& d = "")
        : type(t), message(msg), timestamp(std::chrono::duration_cast<std::chrono::milliseconds>(
            std::chrono::system_clock::now().time_since_epoch()).count()), data(d) {}
};

class VMM {
private:
    VMMConfig config_;
    std::unique_ptr<PageTable> page_table_;
    std::unique_ptr<ReplacementManager> replacement_manager_;
    VMMMetrics metrics_;
    
    // Frame management
    std::vector<bool> frame_validity_;
    std::vector<int> frame_to_page_;
    std::vector<bool> frame_modified_;
    
    // AI Integration
    std::vector<int> recent_accesses_;
    std::vector<int> recent_predictions_;
    static constexpr size_t MAX_RECENT_ACCESSES = 100;
    std::atomic<size_t> ai_predictions_made_{0};
    std::atomic<double> ai_prediction_confidence_{0.0};
    
    // Thread safety
    mutable std::mutex mutex_;
    std::atomic<bool> simulation_running_{false};
    
    // Event callback
    std::function<void(const VMMEvent&)> event_callback_;

public:
    explicit VMM(const VMMConfig& config);
    
    // Core VMM operations
    bool accessPage(int page_number, bool is_write = false);
    void startSimulation();
    void stopSimulation();
    bool isSimulationRunning() const { return simulation_running_; }
    
    // Configuration
    void setConfig(const VMMConfig& config);
    VMMConfig getConfig() const { return config_; }
    
    // Metrics
    size_t getTotalAccesses() const;
    size_t getPageFaults() const;
    size_t getSwapIns() const;
    size_t getSwapOuts() const;
    size_t getAIPredictions() const;
    size_t getAIHits() const;
    double getPageFaultRate() const;
    double getAIHitRate() const;
    double getAIPredictionConfidence() const;
    void resetMetrics();
    
    // Event handling
    void setEventCallback(std::function<void(const VMMEvent&)> callback);
    
    // AI Integration
    std::vector<int> getRecentAccesses() const;
    void setAIPredictions(const std::vector<int>& predicted_pages);
    
    // Utility
    size_t getFreeFrameCount() const;
    size_t getUsedFrameCount() const;
    std::vector<int> getValidPages() const;

private:
    int allocateFrame();
    void deallocateFrame(int frame_number);
    int findFreeFrame() const;
    void handlePageFault(int page_number, bool is_write);
    void swapIn(int page_number, int frame_number);
    void swapOut(int page_number, int frame_number);
    void emitEvent(const std::string& type, const std::string& message, const std::string& data = "");
    void updateRecentAccesses(int page_number);
    std::vector<int> requestAIPredictions();
};

} // namespace vmm
