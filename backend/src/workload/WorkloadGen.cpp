#include "workload/WorkloadGen.h"
#include <algorithm>
#include <cmath>
#include <iostream>

namespace workload {

WorkloadGenerator::WorkloadGenerator(const WorkloadConfig& config) 
    : config_(config), rng_(std::random_device{}()), 
      random_dist_(0, static_cast<int>(config.page_range - 1)),
      prob_dist_(0.0, 1.0) {
    initializeWorkingSet();
}

void WorkloadGenerator::setConfig(const WorkloadConfig& config) {
    config_ = config;
    random_dist_ = std::uniform_int_distribution<int>(0, static_cast<int>(config.page_range - 1));
    initializeWorkingSet();
}

void WorkloadGenerator::start() {
    running_ = true;
    current_position_ = 0;
}

void WorkloadGenerator::stop() {
    running_ = false;
}

void WorkloadGenerator::setAccessCallback(std::function<void(int, bool)> callback) {
    access_callback_ = callback;
}

void WorkloadGenerator::setCompletionCallback(std::function<void()> callback) {
    completion_callback_ = callback;
}

void WorkloadGenerator::generateNextAccess() {
    if (!running_) return;
    
    int page = -1;
    bool is_write = prob_dist_(rng_) < 0.3; // 30% write probability
    
    switch (config_.type) {
        case WorkloadType::SEQUENTIAL:
            page = generateSequentialAccess();
            break;
        case WorkloadType::RANDOM:
            page = generateRandomAccess();
            break;
        case WorkloadType::STRIDED:
            page = generateStridedAccess();
            break;
        case WorkloadType::ZIPF:
            page = generateZipfAccess();
            break;
        case WorkloadType::WEBSERVER:
            page = generateWebserverAccess();
            break;
    }
    
    if (page >= 0 && access_callback_) {
        access_callback_(page, is_write);
    }
    
    current_position_++;
    if (current_position_ >= config_.total_requests) {
        running_ = false;
        if (completion_callback_) {
            completion_callback_();
        }
    }
}

std::vector<int> WorkloadGenerator::generateBatch(size_t batch_size) {
    std::vector<int> batch;
    batch.reserve(batch_size);
    
    for (size_t i = 0; i < batch_size; ++i) {
        int page = -1;
        switch (config_.type) {
            case WorkloadType::SEQUENTIAL:
                page = generateSequentialAccess();
                break;
            case WorkloadType::RANDOM:
                page = generateRandomAccess();
                break;
            case WorkloadType::STRIDED:
                page = generateStridedAccess();
                break;
            case WorkloadType::ZIPF:
                page = generateZipfAccess();
                break;
            case WorkloadType::WEBSERVER:
                page = generateWebserverAccess();
                break;
        }
        if (page >= 0) {
            batch.push_back(page);
        }
    }
    
    return batch;
}

int WorkloadGenerator::generateSequentialAccess() {
    int page = static_cast<int>(current_position_ % config_.page_range);
    return page;
}

int WorkloadGenerator::generateRandomAccess() {
    return random_dist_(rng_);
}

int WorkloadGenerator::generateStridedAccess() {
    int page = static_cast<int>((current_position_ * config_.stride) % config_.page_range);
    return page;
}

int WorkloadGenerator::generateZipfAccess() {
    // Generate rank using Zipf distribution
    double sum = 0.0;
    for (int i = 1; i <= static_cast<int>(config_.page_range); ++i) {
        sum += 1.0 / std::pow(i, config_.zipf_alpha);
    }
    
    double random_value = prob_dist_(rng_) * sum;
    double cumulative = 0.0;
    
    for (int i = 1; i <= static_cast<int>(config_.page_range); ++i) {
        cumulative += 1.0 / std::pow(i, config_.zipf_alpha);
        if (cumulative >= random_value) {
            return i - 1; // Convert to 0-based indexing
        }
    }
    
    return config_.page_range - 1;
}

int WorkloadGenerator::generateWebserverAccess() {
    // Webserver-like access pattern with locality
    if (prob_dist_(rng_) < config_.locality_factor && !working_set_.empty()) {
        // Access working set with high probability
        return selectFromWorkingSet();
    } else {
        // Access random page and add to working set
        int page = random_dist_(rng_);
        updateWorkingSet(page);
        return page;
    }
}

void WorkloadGenerator::initializeWorkingSet() {
    working_set_.clear();
    working_set_.reserve(config_.working_set_size);
    
    // Initialize with random pages
    for (size_t i = 0; i < std::min(config_.working_set_size, config_.page_range); ++i) {
        working_set_.push_back(random_dist_(rng_));
    }
}

void WorkloadGenerator::updateWorkingSet(int page) {
    if (working_set_.size() < config_.working_set_size) {
        working_set_.push_back(page);
    } else {
        // Replace a random page in working set
        std::uniform_int_distribution<size_t> ws_dist(0, working_set_.size() - 1);
        working_set_[ws_dist(rng_)] = page;
    }
}

int WorkloadGenerator::selectFromWorkingSet() {
    if (working_set_.empty()) {
        return random_dist_(rng_);
    }
    
    std::uniform_int_distribution<size_t> ws_dist(0, working_set_.size() - 1);
    return working_set_[ws_dist(rng_)];
}

double WorkloadGenerator::calculateZipfProbability(int rank) const {
    return 1.0 / std::pow(rank, config_.zipf_alpha);
}

void WorkloadGenerator::reset() {
    current_position_ = 0;
    initializeWorkingSet();
}

std::string WorkloadGenerator::getWorkloadDescription() const {
    switch (config_.type) {
        case WorkloadType::SEQUENTIAL:
            return "Sequential access pattern";
        case WorkloadType::RANDOM:
            return "Random access pattern";
        case WorkloadType::STRIDED:
            return "Strided access pattern (stride=" + std::to_string(config_.stride) + ")";
        case WorkloadType::ZIPF:
            return "Zipf distribution (alpha=" + std::to_string(config_.zipf_alpha) + ")";
        case WorkloadType::WEBSERVER:
            return "Webserver-like access pattern (locality=" + std::to_string(config_.locality_factor) + ")";
        default:
            return "Unknown workload type";
    }
}

} // namespace workload
