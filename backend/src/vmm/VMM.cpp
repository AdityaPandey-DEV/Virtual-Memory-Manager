#include "vmm/VMM.h"
#include <algorithm>
#include <random>
#include <iostream>

namespace vmm {

VMM::VMM(const VMMConfig& config) : config_(config) {
    // Initialize page table
    page_table_ = std::make_unique<PageTable>(config_.page_size, config_.total_pages);
    
    // Initialize replacement manager
    replacement_manager_ = std::make_unique<ReplacementManager>(
        config_.replacement_policy, config_.total_frames);
    
    // Initialize frame management
    frame_validity_.resize(config_.total_frames, false);
    frame_to_page_.resize(config_.total_frames, -1);
    frame_modified_.resize(config_.total_frames, false);
}

bool VMM::accessPage(int page_number, bool is_write) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    if (!simulation_running_) {
        return false;
    }
    
    metrics_.total_accesses++;
    updateRecentAccesses(page_number);
    
    // Request AI predictions for prefetching
    if (config_.enable_ai_predictions && recent_accesses_.size() >= 3) {
        std::vector<int> predictions = requestAIPredictions();
        if (!predictions.empty()) {
            // Prefetch predicted pages
            for (int predicted_page : predictions) {
                if (predicted_page != page_number && !page_table_->isPageValid(predicted_page)) {
                    // Check if we have free frames for prefetching
                    int free_frame = findFreeFrame();
                    if (free_frame != -1) {
                        swapIn(predicted_page, free_frame);
                        emitEvent("AI", "Prefetched page " + std::to_string(predicted_page) + " based on AI prediction");
                    }
                }
            }
        }
    }
    
    // Check if page is in memory
    if (page_table_->isPageValid(page_number)) {
        int frame_number = page_table_->getFrameNumber(page_number);
        page_table_->recordPageAccess(page_number, metrics_.total_accesses);
        replacement_manager_->recordFrameAccess(frame_number);
        
        // Check if this was a successful AI prediction
        if (config_.enable_ai_predictions && !recent_predictions_.empty()) {
            // Check if this page was in our recent predictions
            auto it = std::find(recent_predictions_.begin(), recent_predictions_.end(), page_number);
            if (it != recent_predictions_.end()) {
                metrics_.ai_hits++;
                emitEvent("AI", "AI HIT: Page " + std::to_string(page_number) + " was correctly predicted!");
                // Remove this prediction from the list to avoid double counting
                recent_predictions_.erase(it);
            }
        }
        
        if (is_write) {
            page_table_->setPageModified(page_number, true);
            frame_modified_[frame_number] = true;
        }
        
        emitEvent("ACCESS", "Page " + std::to_string(page_number) + 
                  (is_write ? " (write)" : " (read)"));
        return true;
    }
    
    // Page fault occurred
    handlePageFault(page_number, is_write);
    return true;
}

void VMM::startSimulation() {
    std::lock_guard<std::mutex> lock(mutex_);
    simulation_running_ = true;
    emitEvent("SIMULATION", "Simulation started");
}

void VMM::stopSimulation() {
    std::lock_guard<std::mutex> lock(mutex_);
    simulation_running_ = false;
    emitEvent("SIMULATION", "Simulation stopped");
}

void VMM::setConfig(const VMMConfig& config) {
    std::lock_guard<std::mutex> lock(mutex_);
    config_ = config;
    
    // Reinitialize components with new config
    page_table_ = std::make_unique<PageTable>(config_.page_size, config_.total_pages);
    replacement_manager_ = std::make_unique<ReplacementManager>(
        config_.replacement_policy, config_.total_frames);
    
    frame_validity_.resize(config_.total_frames, false);
    frame_to_page_.resize(config_.total_frames, -1);
    frame_modified_.resize(config_.total_frames, false);
}

size_t VMM::getTotalAccesses() const {
    return metrics_.total_accesses.load();
}

size_t VMM::getPageFaults() const {
    return metrics_.page_faults.load();
}

size_t VMM::getSwapIns() const {
    return metrics_.swap_ins.load();
}

size_t VMM::getSwapOuts() const {
    return metrics_.swap_outs.load();
}

size_t VMM::getAIPredictions() const {
    return metrics_.ai_predictions.load();
}

size_t VMM::getAIHits() const {
    return metrics_.ai_hits.load();
}

double VMM::getPageFaultRate() const {
    size_t total = metrics_.total_accesses.load();
    return total > 0 ? static_cast<double>(metrics_.page_faults.load()) / total : 0.0;
}

double VMM::getAIHitRate() const {
    size_t predictions = metrics_.ai_predictions.load();
    return predictions > 0 ? static_cast<double>(metrics_.ai_hits.load()) / predictions : 0.0;
}

double VMM::getAIPredictionConfidence() const {
    return ai_prediction_confidence_.load();
}

void VMM::resetMetrics() {
    std::lock_guard<std::mutex> lock(mutex_);
    metrics_.total_accesses = 0;
    metrics_.page_faults = 0;
    metrics_.swap_ins = 0;
    metrics_.swap_outs = 0;
    metrics_.ai_predictions = 0;
    metrics_.ai_hits = 0;
}

void VMM::setEventCallback(std::function<void(const VMMEvent&)> callback) {
    std::lock_guard<std::mutex> lock(mutex_);
    event_callback_ = callback;
}

std::vector<int> VMM::getRecentAccesses() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return recent_accesses_;
}

void VMM::setAIPredictions(const std::vector<int>& predicted_pages) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    metrics_.ai_predictions++;
    emitEvent("AI", "Received " + std::to_string(predicted_pages.size()) + " predictions");
    
    // Prefetch predicted pages if they're not already in memory
    for (int page : predicted_pages) {
        if (!page_table_->isPageValid(page)) {
            int free_frame = findFreeFrame();
            if (free_frame != -1) {
                swapIn(page, free_frame);
                metrics_.ai_hits++;
                emitEvent("AI", "Prefetched page " + std::to_string(page));
            }
        }
    }
}

size_t VMM::getFreeFrameCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return std::count(frame_validity_.begin(), frame_validity_.end(), false);
}

size_t VMM::getUsedFrameCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return std::count(frame_validity_.begin(), frame_validity_.end(), true);
}

std::vector<int> VMM::getValidPages() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return page_table_->getValidPages();
}

int VMM::allocateFrame() {
    int free_frame = findFreeFrame();
    if (free_frame != -1) {
        frame_validity_[free_frame] = true;
        frame_modified_[free_frame] = false;
        return free_frame;
    }
    return -1;
}

void VMM::deallocateFrame(int frame_number) {
    if (frame_number >= 0 && frame_number < static_cast<int>(frame_validity_.size())) {
        frame_validity_[frame_number] = false;
        frame_to_page_[frame_number] = -1;
        frame_modified_[frame_number] = false;
    }
}

int VMM::findFreeFrame() const {
    for (size_t i = 0; i < frame_validity_.size(); ++i) {
        if (!frame_validity_[i]) {
            return static_cast<int>(i);
        }
    }
    return -1;
}

void VMM::handlePageFault(int page_number, bool is_write) {
    metrics_.page_faults++;
    emitEvent("FAULT", "Page fault for page " + std::to_string(page_number));
    
    int frame_number = allocateFrame();
    if (frame_number == -1) {
        // No free frames, need to evict
        frame_number = replacement_manager_->selectVictimFrame(frame_validity_, *page_table_);
        if (frame_number == -1) {
            emitEvent("ERROR", "No victim frame found");
            return;
        }
        
        // Evict the victim page
        int victim_page = frame_to_page_[frame_number];
        if (victim_page != -1) {
            page_table_->setPageValid(victim_page, false);
            if (frame_modified_[frame_number]) {
                swapOut(victim_page, frame_number);
            }
            emitEvent("EVICT", "Evicted page " + std::to_string(victim_page) + 
                      " from frame " + std::to_string(frame_number));
        }
    }
    
    // Load the new page
    swapIn(page_number, frame_number);
    page_table_->setPageValid(page_number, true);
    page_table_->setFrameNumber(page_number, frame_number);
    page_table_->recordPageAccess(page_number, metrics_.total_accesses);
    
    if (is_write) {
        page_table_->setPageModified(page_number, true);
        frame_modified_[frame_number] = true;
    }
    
    frame_to_page_[frame_number] = page_number;
    replacement_manager_->recordFrameAccess(frame_number);
}

void VMM::swapIn(int page_number, int frame_number) {
    metrics_.swap_ins++;
    emitEvent("SWAP_IN", "Swapped in page " + std::to_string(page_number) + 
              " to frame " + std::to_string(frame_number));
}

void VMM::swapOut(int page_number, int frame_number) {
    metrics_.swap_outs++;
    emitEvent("SWAP_OUT", "Swapped out page " + std::to_string(page_number) + 
              " from frame " + std::to_string(frame_number));
}

void VMM::emitEvent(const std::string& type, const std::string& message, const std::string& data) {
    if (event_callback_) {
        VMMEvent event(type, message, data);
        event_callback_(event);
    }
}

void VMM::updateRecentAccesses(int page_number) {
    recent_accesses_.push_back(page_number);
    if (recent_accesses_.size() > MAX_RECENT_ACCESSES) {
        recent_accesses_.erase(recent_accesses_.begin());
    }
}

std::vector<int> VMM::requestAIPredictions() {
    std::cout << "AI Prediction Request - enable_ai_predictions: " << config_.enable_ai_predictions 
              << ", recent_accesses size: " << recent_accesses_.size() << std::endl;
    
    if (!config_.enable_ai_predictions || recent_accesses_.empty()) {
        return {};
    }
    
    std::vector<int> predictions;
    
    try {
        // Simulate AI prediction with realistic patterns
        if (recent_accesses_.size() >= 3) {
            int last_page = recent_accesses_.back();
            int second_last = recent_accesses_[recent_accesses_.size() - 2];
            int third_last = recent_accesses_[recent_accesses_.size() - 3];
            
            // Pattern 1: Sequential access (high confidence)
            if (last_page == second_last + 1 && second_last == third_last + 1) {
                predictions.push_back((last_page + 1) % config_.total_pages);
                predictions.push_back((last_page + 2) % config_.total_pages);
                ai_prediction_confidence_ = 0.85;
            }
            // Pattern 2: Strided access (medium confidence)
            else if (last_page - second_last == second_last - third_last) {
                int stride = last_page - second_last;
                predictions.push_back((last_page + stride) % config_.total_pages);
                predictions.push_back((last_page + 2 * stride) % config_.total_pages);
                ai_prediction_confidence_ = 0.70;
            }
            // Pattern 3: Locality-based (medium confidence)
            else {
                // Predict pages in the same locality
                int base = (last_page / 10) * 10;
                predictions.push_back((base + (last_page % 10 + 1) % 10) % config_.total_pages);
                predictions.push_back((base + (last_page % 10 + 2) % 10) % config_.total_pages);
                ai_prediction_confidence_ = 0.60;
            }
            
            // Add some random predictions for variety
            if (predictions.size() < 3) {
                predictions.push_back((last_page + 3) % config_.total_pages);
            }
        }
        
        // Update AI metrics
        if (!predictions.empty()) {
            ai_predictions_made_++;
            metrics_.ai_predictions++;
            
            // Store predictions for hit tracking
            recent_predictions_.insert(recent_predictions_.end(), predictions.begin(), predictions.end());
            
            // Keep only recent predictions (last 50 to avoid memory buildup)
            if (recent_predictions_.size() > 50) {
                recent_predictions_.erase(recent_predictions_.begin(), recent_predictions_.begin() + (recent_predictions_.size() - 50));
            }
            
            std::cout << "AI Predictions made: " << predictions.size() << ", total: " << metrics_.ai_predictions << std::endl;
            // Send prediction data in format expected by frontend
            std::string prediction_data = "Predicted {";
            for (size_t i = 0; i < predictions.size(); ++i) {
                if (i > 0) prediction_data += ", ";
                prediction_data += std::to_string(predictions[i]);
            }
            prediction_data += "}";
            
            emitEvent("AI", prediction_data);
            emitEvent("AI", "Generated " + std::to_string(predictions.size()) + " predictions (confidence: " + 
                     std::to_string(ai_prediction_confidence_) + ")");
        }
        
    } catch (const std::exception& e) {
        emitEvent("AI", "Prediction failed: " + std::string(e.what()));
        ai_prediction_confidence_ = 0.0;
    }
    
    return predictions;
}

} // namespace vmm
