#include "vmm/Replacement.h"
#include <algorithm>
#include <climits>

namespace vmm {

// FIFO Implementation
int FIFOReplacement::selectVictimFrame(const std::vector<bool>& frame_validity, 
                                       const PageTable& page_table) {
    // Find the first frame that's valid and in our queue
    while (!fifo_queue_.empty()) {
        int frame = fifo_queue_.front();
        if (frame_validity[frame]) {
            return frame;
        }
        fifo_queue_.pop();
        in_queue_.erase(frame);
    }
    return -1; // No victim found
}

void FIFOReplacement::recordFrameAccess(int frame_number) {
    if (in_queue_.find(frame_number) == in_queue_.end()) {
        fifo_queue_.push(frame_number);
        in_queue_.insert(frame_number);
    }
}

void FIFOReplacement::recordFrameEviction(int frame_number) {
    // FIFO doesn't need special handling for evictions
}

// LRU Implementation
LRUReplacement::LRUReplacement(size_t num_frames) 
    : last_access_times_(num_frames, 0) {
}

int LRUReplacement::selectVictimFrame(const std::vector<bool>& frame_validity, 
                                      const PageTable& page_table) {
    size_t oldest_time = ULLONG_MAX;
    int victim_frame = -1;
    
    for (size_t i = 0; i < frame_validity.size(); ++i) {
        if (frame_validity[i] && last_access_times_[i] < oldest_time) {
            oldest_time = last_access_times_[i];
            victim_frame = static_cast<int>(i);
        }
    }
    
    return victim_frame;
}

void LRUReplacement::recordFrameAccess(int frame_number) {
    if (frame_number >= 0 && frame_number < static_cast<int>(last_access_times_.size())) {
        last_access_times_[frame_number] = current_time_++;
    }
}

void LRUReplacement::recordFrameEviction(int frame_number) {
    // LRU doesn't need special handling for evictions
}

// CLOCK Implementation
CLOCKReplacement::CLOCKReplacement(size_t num_frames) 
    : reference_bits_(num_frames, false) {
}

int CLOCKReplacement::selectVictimFrame(const std::vector<bool>& frame_validity, 
                                        const PageTable& page_table) {
    int start_hand = clock_hand_;
    
    // First pass: look for unreferenced frame
    do {
        if (frame_validity[clock_hand_] && !reference_bits_[clock_hand_]) {
            int victim = clock_hand_;
            clock_hand_ = (clock_hand_ + 1) % frame_validity.size();
            return victim;
        }
        clock_hand_ = (clock_hand_ + 1) % frame_validity.size();
    } while (clock_hand_ != start_hand);
    
    // Second pass: clear reference bits and find victim
    do {
        if (frame_validity[clock_hand_]) {
            if (!reference_bits_[clock_hand_]) {
                int victim = clock_hand_;
                clock_hand_ = (clock_hand_ + 1) % frame_validity.size();
                return victim;
            } else {
                reference_bits_[clock_hand_] = false;
            }
        }
        clock_hand_ = (clock_hand_ + 1) % frame_validity.size();
    } while (clock_hand_ != start_hand);
    
    return -1; // No victim found
}

void CLOCKReplacement::recordFrameAccess(int frame_number) {
    if (frame_number >= 0 && frame_number < static_cast<int>(reference_bits_.size())) {
        reference_bits_[frame_number] = true;
    }
}

void CLOCKReplacement::recordFrameEviction(int frame_number) {
    if (frame_number >= 0 && frame_number < static_cast<int>(reference_bits_.size())) {
        reference_bits_[frame_number] = false;
    }
}

// ReplacementManager Implementation
ReplacementManager::ReplacementManager(ReplacementPolicy policy, size_t num_frames) 
    : num_frames_(num_frames) {
    setPolicy(policy);
}

int ReplacementManager::selectVictimFrame(const std::vector<bool>& frame_validity, 
                                         const PageTable& page_table) {
    return algorithm_->selectVictimFrame(frame_validity, page_table);
}

void ReplacementManager::recordFrameAccess(int frame_number) {
    algorithm_->recordFrameAccess(frame_number);
}

void ReplacementManager::recordFrameEviction(int frame_number) {
    algorithm_->recordFrameEviction(frame_number);
}

std::string ReplacementManager::getPolicyName() const {
    return algorithm_->getPolicyName();
}

void ReplacementManager::setPolicy(ReplacementPolicy policy) {
    switch (policy) {
        case ReplacementPolicy::FIFO:
            algorithm_ = std::make_unique<FIFOReplacement>();
            break;
        case ReplacementPolicy::LRU:
            algorithm_ = std::make_unique<LRUReplacement>(num_frames_);
            break;
        case ReplacementPolicy::CLOCK:
            algorithm_ = std::make_unique<CLOCKReplacement>(num_frames_);
            break;
    }
}

} // namespace vmm
