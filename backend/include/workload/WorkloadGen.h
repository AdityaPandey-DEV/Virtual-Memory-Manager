#pragma once

#include <vector>
#include <string>
#include <random>
#include <functional>
#include <atomic>

namespace workload {

enum class WorkloadType {
    SEQUENTIAL,
    RANDOM,
    STRIDED,
    ZIPF,
    WEBSERVER
};

struct WorkloadConfig {
    WorkloadType type = WorkloadType::RANDOM;
    size_t total_requests = 1000;
    size_t page_range = 1000;
    int stride = 1;
    double zipf_alpha = 1.0;
    double locality_factor = 0.8;
    size_t working_set_size = 100;
};

class WorkloadGenerator {
private:
    WorkloadConfig config_;
    std::mt19937 rng_;
    std::atomic<bool> running_{false};
    std::function<void(int, bool)> access_callback_;
    std::function<void()> completion_callback_;
    
    // Workload-specific state
    size_t current_position_ = 0;
    std::vector<int> working_set_;
    std::uniform_int_distribution<int> random_dist_;
    std::uniform_real_distribution<double> prob_dist_;

public:
    explicit WorkloadGenerator(const WorkloadConfig& config);
    
    // Configuration
    void setConfig(const WorkloadConfig& config);
    WorkloadConfig getConfig() const { return config_; }
    
    // Control
    void start();
    void stop();
    bool isRunning() const { return running_; }
    
    // Callbacks
    void setAccessCallback(std::function<void(int, bool)> callback);
    void setCompletionCallback(std::function<void()> callback);
    
    // Workload generation
    void generateNextAccess();
    std::vector<int> generateBatch(size_t batch_size);
    
    // Workload-specific methods
    int generateSequentialAccess();
    int generateRandomAccess();
    int generateStridedAccess();
    int generateZipfAccess();
    int generateWebserverAccess();
    
    // Utility
    void reset();
    std::string getWorkloadDescription() const;

private:
    void initializeWorkingSet();
    void updateWorkingSet(int page);
    int selectFromWorkingSet();
    double calculateZipfProbability(int rank) const;
};

} // namespace workload
