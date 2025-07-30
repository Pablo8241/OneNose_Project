#include "enose_functions.h"
#include <algorithm>
#include <chrono>
#include <thread>

// Normalize function - equivalent to Python version
double normalize(double value, double min_val, double max_val) {
    return std::max(0.0, std::min(1.0, (value - min_val) / (max_val - min_val)));
}

// Create RGB color value
int createColor(int r, int g, int b) {
    return (r << 16) | (g << 8) | b;
}

// LED animation function - color wipe across display
void colorWipe(int strip_pin, int led_count, int color, int wait_ms) {
    // Placeholder implementation for testing without hardware
    std::cout << "ColorWipe: pin=" << strip_pin << ", count=" << led_count 
              << ", color=0x" << std::hex << color << std::dec 
              << ", wait=" << wait_ms << "ms" << std::endl;
    
    for (int i = 0; i < led_count; i++) {
        std::cout << "Setting LED " << i << " to color 0x" << std::hex << color << std::dec << std::endl;
        std::this_thread::sleep_for(std::chrono::milliseconds(wait_ms));
    }
    
    // Note: Real implementation would use:
    // ws2811_t ledstring;
    // Initialize ledstring...
    // For each LED: ws2811_led_set(&ledstring, 0, i, color);
    // ws2811_render(&ledstring);
}
