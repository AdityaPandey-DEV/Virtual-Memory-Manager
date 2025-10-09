#pragma once

#include <unordered_map>
#include <vector>
#include <memory>
#include <mutex>

namespace vmm {

struct PageEntry {
    bool valid = false;
    bool referenced = false;
    bool modified = false;
    int frame_number = -1;
    int access_count = 0;
    size_t last_access_time = 0;
    
    PageEntry() = default;
    PageEntry(bool v, bool r, bool m, int f) 
        : valid(v), referenced(r), modified(m), frame_number(f) {}
};

class PageTable {
private:
    std::unordered_map<int, PageEntry> pages_;
    mutable std::mutex mutex_;
    size_t page_size_;
    size_t total_pages_;

public:
    explicit PageTable(size_t page_size = 4096, size_t total_pages = 1024);
    
    // Page table operations
    bool isPageValid(int page_number) const;
    bool isPageReferenced(int page_number) const;
    bool isPageModified(int page_number) const;
    int getFrameNumber(int page_number) const;
    
    void setPageValid(int page_number, bool valid);
    void setPageReferenced(int page_number, bool referenced);
    void setPageModified(int page_number, bool modified);
    void setFrameNumber(int page_number, int frame_number);
    
    // Access tracking
    void recordPageAccess(int page_number, size_t current_time);
    int getAccessCount(int page_number) const;
    size_t getLastAccessTime(int page_number) const;
    
    // Utility functions
    size_t getPageSize() const { return page_size_; }
    size_t getTotalPages() const { return total_pages_; }
    size_t getValidPageCount() const;
    
    // Get all valid pages (for AI predictions)
    std::vector<int> getValidPages() const;
    
    // Clear page table
    void clear();
    
    // Thread-safe access
    std::lock_guard<std::mutex> getLock() const;
};

} // namespace vmm
