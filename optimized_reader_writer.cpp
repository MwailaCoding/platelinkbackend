#include <iostream>
#include <thread>
#include <shared_mutex>
#include <mutex>
#include <vector>
#include <chrono>

int sharedData = 0;
std::shared_mutex shMtx;
std::mutex coutMtx; // Mutex to serialize standard output and prevent interleaving

void reader(int id) {
    for (int i = 0; i < 5; ++i) {
        // Read lock (shared ownership) via RAII
        {
            std::shared_lock<std::shared_mutex> lock(shMtx);
            
            // Protect std::cout print operations
            std::lock_guard<std::mutex> printLock(coutMtx);
            std::cout << "Reader " << id << " read: " << sharedData << std::endl;
        } // lock is automatically released here before sleep
        
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
}

void writer(int id) {
    for (int i = 0; i < 5; ++i) {
        // Write lock (exclusive ownership) via RAII
        {
            std::unique_lock<std::shared_mutex> lock(shMtx);
            sharedData++;
            
            // Protect std::cout print operations
            std::lock_guard<std::mutex> printLock(coutMtx);
            std::cout << "Writer " << id << " updated to: " << sharedData << std::endl;
        } // lock is automatically released here before sleep
        
        std::this_thread::sleep_for(std::chrono::milliseconds(100));
    }
}

int main() {
    std::vector<std::thread> threads;
    
    // Spawn reader threads
    for (int i = 0; i < 3; ++i) {
        threads.push_back(std::thread(reader, i));
    }
    
    // Spawn writer threads
    for (int i = 0; i < 2; ++i) {
        threads.push_back(std::thread(writer, i));
    }

    // Join all threads
    for (auto& t : threads) {
        t.join();
    }
    
    return 0;
}
