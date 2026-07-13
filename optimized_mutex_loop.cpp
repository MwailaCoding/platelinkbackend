#include <iostream>
#include <thread>
#include <mutex>
#include <chrono>

int main() {
    int sharedVar = 0;
    std::mutex mtx;

    // Optimized worker using local accumulator to minimize lock contention
    auto work = [&]() {
        int localSum = 0;
        for (int i = 0; i < 1000; ++i) {
            localSum++;
        }
        
        // Lock only once at the end of the loop
        std::lock_guard<std::mutex> lock(mtx);
        sharedVar += localSum;
    };

    auto start = std::chrono::high_resolution_clock::now();

    std::thread t1(work);
    std::thread t2(work);

    t1.join();
    t2.join();

    auto end = std::chrono::high_resolution_clock::now();
    std::chrono::duration<double, std::milli> duration = end - start;

    std::cout << "sharedVar: " << sharedVar << " (Expected: 2000)" << std::endl;
    std::cout << "Time taken: " << duration.count() << " ms" << std::endl;
    
    return 0;
}
