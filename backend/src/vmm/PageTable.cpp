#include "vmm/PageTable.h"
#include <algorithm>

namespace vmm {

PageTable::PageTable(size_t page_size, size_t total_pages) 
    : page_size_(page_size), total_pages_(total_pages) {
}

bool PageTable::isPageValid(int page_number) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = pages_.find(page_number);
    return it != pages_.end() && it->second.valid;
}

bool PageTable::isPageReferenced(int page_number) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = pages_.find(page_number);
    return it != pages_.end() && it->second.referenced;
}

bool PageTable::isPageModified(int page_number) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = pages_.find(page_number);
    return it != pages_.end() && it->second.modified;
}

int PageTable::getFrameNumber(int page_number) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = pages_.find(page_number);
    return (it != pages_.end() && it->second.valid) ? it->second.frame_number : -1;
}

void PageTable::setPageValid(int page_number, bool valid) {
    std::lock_guard<std::mutex> lock(mutex_);
    pages_[page_number].valid = valid;
}

void PageTable::setPageReferenced(int page_number, bool referenced) {
    std::lock_guard<std::mutex> lock(mutex_);
    pages_[page_number].referenced = referenced;
}

void PageTable::setPageModified(int page_number, bool modified) {
    std::lock_guard<std::mutex> lock(mutex_);
    pages_[page_number].modified = modified;
}

void PageTable::setFrameNumber(int page_number, int frame_number) {
    std::lock_guard<std::mutex> lock(mutex_);
    pages_[page_number].frame_number = frame_number;
}

void PageTable::recordPageAccess(int page_number, size_t current_time) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto& entry = pages_[page_number];
    entry.referenced = true;
    entry.access_count++;
    entry.last_access_time = current_time;
}

int PageTable::getAccessCount(int page_number) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = pages_.find(page_number);
    return (it != pages_.end()) ? it->second.access_count : 0;
}

size_t PageTable::getLastAccessTime(int page_number) const {
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = pages_.find(page_number);
    return (it != pages_.end()) ? it->second.last_access_time : 0;
}

size_t PageTable::getValidPageCount() const {
    std::lock_guard<std::mutex> lock(mutex_);
    size_t count = 0;
    for (const auto& pair : pages_) {
        if (pair.second.valid) {
            count++;
        }
    }
    return count;
}

std::vector<int> PageTable::getValidPages() const {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<int> valid_pages;
    for (const auto& pair : pages_) {
        if (pair.second.valid) {
            valid_pages.push_back(pair.first);
        }
    }
    return valid_pages;
}

void PageTable::clear() {
    std::lock_guard<std::mutex> lock(mutex_);
    pages_.clear();
}

std::lock_guard<std::mutex> PageTable::getLock() const {
    return std::lock_guard<std::mutex>(mutex_);
}

} // namespace vmm
