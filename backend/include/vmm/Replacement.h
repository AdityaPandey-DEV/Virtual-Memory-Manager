#pragma once

#include <vector>
#include <queue>
#include <unordered_set>
#include <memory>
#include "PageTable.h"

namespace vmm {

enum class ReplacementPolicy {
    FIFO,
    LRU,
    CLOCK
};

class ReplacementAlgorithm {
public:
    virtual ~ReplacementAlgorithm() = default;
    virtual int selectVictimFrame(const std::vector<bool>& frame_validity, 
                                 const PageTable& page_table) = 0;
    virtual void recordFrameAccess(int frame_number) = 0;
    virtual void recordFrameEviction(int frame_number) = 0;
    virtual std::string getPolicyName() const = 0;
};

class FIFOReplacement : public ReplacementAlgorithm {
private:
    std::queue<int> fifo_queue_;
    std::unordered_set<int> in_queue_;

public:
    int selectVictimFrame(const std::vector<bool>& frame_validity, 
                         const PageTable& page_table) override;
    void recordFrameAccess(int frame_number) override;
    void recordFrameEviction(int frame_number) override;
    std::string getPolicyName() const override { return "FIFO"; }
};

class LRUReplacement : public ReplacementAlgorithm {
private:
    std::vector<size_t> last_access_times_;
    size_t current_time_ = 0;

public:
    explicit LRUReplacement(size_t num_frames);
    int selectVictimFrame(const std::vector<bool>& frame_validity, 
                         const PageTable& page_table) override;
    void recordFrameAccess(int frame_number) override;
    void recordFrameEviction(int frame_number) override;
    std::string getPolicyName() const override { return "LRU"; }
};

class CLOCKReplacement : public ReplacementAlgorithm {
private:
    std::vector<bool> reference_bits_;
    int clock_hand_ = 0;

public:
    explicit CLOCKReplacement(size_t num_frames);
    int selectVictimFrame(const std::vector<bool>& frame_validity, 
                         const PageTable& page_table) override;
    void recordFrameAccess(int frame_number) override;
    void recordFrameEviction(int frame_number) override;
    std::string getPolicyName() const override { return "CLOCK"; }
};

class ReplacementManager {
private:
    std::unique_ptr<ReplacementAlgorithm> algorithm_;
    size_t num_frames_;

public:
    explicit ReplacementManager(ReplacementPolicy policy, size_t num_frames);
    
    int selectVictimFrame(const std::vector<bool>& frame_validity, 
                         const PageTable& page_table);
    void recordFrameAccess(int frame_number);
    void recordFrameEviction(int frame_number);
    std::string getPolicyName() const;
    
    void setPolicy(ReplacementPolicy policy);
};

} // namespace vmm
