#include <iostream>
#include <vector>
#include <thread>
#include <atomic>
#include <chrono>
#include <map>
#include <string>
#include <cstdlib>
#include <memory>
#include <exception>
#include "enose_functions.h"

// Hardware control libraries (need to be installed)
#include <wiringPi.h>           // GPIO control (equivalent to RPi.GPIO)
#include <wiringPiI2C.h>        // I2C communication
#include <ws2811.h>             // LED control (rpi_ws281x)
// #include <bme680.h>          // BME680 sensor (custom or third-party)
// #include <sgp30.h>           // SGP30 sensor (custom or third-party)  
// #include <tca9548a.h>        // I2C multiplexer (custom or third-party)

// GUI library (choose one)
// #include <gtk/gtk.h>         // GTK+ for GUI
// #include <QtWidgets>         // Qt for GUI

// Note: Some sensor libraries may need to be custom-built or found as third-party
// The hardware control libraries (wiringPi, ws2811) are standard for Raspberry Pi

class DirectionalENose {
private:
    // Constants
    static const int PIN = 12;  // Grove WS2813 RGB LED Strip SIG pin
    static const int COUNT = 20; // Grove - WS2813 RGB LED Ring - 20 LED total
    
    // Thread control
    std::atomic<bool> stop_event{false};
    std::atomic<bool> shutdown{false};
    
    // Sensor data storage
    std::vector<int> co2_readings;
    std::vector<int> tvoc_readings;
    std::vector<double> combined_scores;
    
    // Sensor to LED mapping
    std::map<int, int> sensor_to_led_map = {
        {0, 1},   // Sensor 0 → LED 1
        {1, 5},   // Sensor 1 → LED 5
        {2, 11},  // Sensor 2 → LED 11
        {3, 15}   // Sensor 3 → LED 15
    };
    
    // GUI components (placeholder - would need actual GUI library)
    std::string label3_text = "Awaiting sensor data...";
    
public:
    DirectionalENose() {
        co2_readings.reserve(10);
        tvoc_readings.reserve(10);
        combined_scores.reserve(10);
    }
    
    ~DirectionalENose() {
        cleanup();
    }
    
    void program_init() {
        std::cout << "Initializing Directional eNose..." << std::endl;
        
        // Initialize wiringPi
        if (wiringPiSetup() == -1) {
            std::cerr << "Failed to initialize wiringPi" << std::endl;
            // Don't throw - just continue without GPIO for testing
        } else {
            std::cout << "WiringPi initialized successfully" << std::endl;
            
            // GPIO setup for buttons
            pinMode(27, INPUT);
            pullUpDnControl(27, PUD_UP);  // Shutdown trigger
            pinMode(17, INPUT);
            pullUpDnControl(17, PUD_UP);  // Normal exit
            std::cout << "GPIO pins configured" << std::endl;
        }
        
        // BME680 sensor initialization
        init_bme680();
        
        // SGP30 sensors initialization
        std::cout << "Initializing SGP30 sensors..." << std::endl;
        init_sgp30_sensors();
        
        // Start button polling thread
        std::thread button_thread(&DirectionalENose::button_polling_loop, this);
        button_thread.detach();
        
        std::cout << "Testing LED ring functionality with a color wipe animation." << std::endl;
        colorWipe(PIN, COUNT, createColor(0, 255, 0)); // Green wipe
    }
    
    void sensor_loop() {
        while (!stop_event.load()) {
            co2_readings.clear();
            tvoc_readings.clear();
            combined_scores.clear();
            
            // Read SGP30 sensor data
            for (int i = 0; i < 10; i++) {
                try {
                    // Read sensor data (placeholder - would need actual I2C communication)
                    auto [co2, tvoc] = read_sgp30_sensor(i);
                    
                    co2_readings.push_back(co2);
                    tvoc_readings.push_back(tvoc);
                    
                    // Normalize readings
                    double norm_co2 = normalize(co2, 400, 60000);   // CO2 from 400ppm to 60000ppm
                    double norm_tvoc = normalize(tvoc, 0, 60000);   // TVOC from 0ppb to 60000ppb
                    double score = norm_co2 + norm_tvoc;            // Combined score
                    
                    combined_scores.push_back(score);
                } catch (const std::exception& e) {
                    std::cout << "Error reading SGP30_" << (i+1) << ": " << e.what() << std::endl;
                    co2_readings.push_back(-1);
                    tvoc_readings.push_back(-1);
                    combined_scores.push_back(-1.0); // Force it to be lowest
                }
            }
            
            // Find sensor with highest readings (only outer 4 sensors)
            std::vector<double> outer_scores(combined_scores.begin(), combined_scores.begin() + 4);
            
            auto max_it = std::max_element(outer_scores.begin(), outer_scores.end());
            int highest_index = std::distance(outer_scores.begin(), max_it);
            
            std::cout << "Sensor with highest readings (outer 4 only): SGP30_" << (highest_index + 1) << std::endl;
            
            // Update GUI label (placeholder)
            label3_text = "Highest: SGP30_" + std::to_string(highest_index + 1);
            
            // Control LEDs
            auto highlight_led_it = sensor_to_led_map.find(highest_index);
            
            // Turn off all LEDs
            clear_all_leds();
            
            // Highlight LED if valid
            if (highlight_led_it != sensor_to_led_map.end()) {
                int highlight_led = highlight_led_it->second;
                set_led_color(highlight_led, createColor(255, 0, 0)); // Red highlight
            }
            
            // Print sensor data
            print_sensor_data();
            
            // Read BME680 sensor data
            read_bme680_data();
            
            // Wait 1 second (minimum required for SGP30)
            std::this_thread::sleep_for(std::chrono::seconds(1));
        }
    }
    
    void start_gui() {
        std::cout << "Starting GUI (placeholder - would use GTK+ or Qt)" << std::endl;
        
        // Placeholder for GUI creation
        // In a real implementation, you would use GTK+ or Qt to create:
        // - Fullscreen window
        // - "OneNose" title label
        // - "Directional Electronic Nose" subtitle
        // - Dynamic sensor status label
        // - "Bind smell to this label" instruction
        
        // For now, just simulate the main loop
        while (!stop_event.load()) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
    
    void on_closing() {
        std::cout << "Closing app..." << std::endl;
        
        stop_event.store(true);
        
        // Small shutdown animation
        colorWipe(PIN, COUNT, createColor(255, 0, 0)); // Red wipe
        
        // Turn off all LEDs
        clear_all_leds();
        
        // Close GUI (placeholder)
        std::cout << "GUI closed." << std::endl;
    }
    
    void button_polling_loop() {
        bool prev_state_27 = true; // Assuming pull-up, so HIGH when not pressed
        bool prev_state_17 = true;
        
        while (!stop_event.load()) {
            // Read GPIO states (placeholder - would use actual GPIO library)
            bool curr_state_27 = read_gpio(27);
            bool curr_state_17 = read_gpio(17);
            
            // Detect button press (falling edge)
            if (prev_state_27 && !curr_state_27) {
                std::cout << "GPIO 27 pressed – triggering shutdown." << std::endl;
                shutdown.store(true);
                on_closing();
            }
            
            if (prev_state_17 && !curr_state_17) {
                std::cout << "GPIO 17 pressed – exiting app without shutdown." << std::endl;
                shutdown.store(false);
                on_closing();
            }
            
            prev_state_27 = curr_state_27;
            prev_state_17 = curr_state_17;
            
            std::this_thread::sleep_for(std::chrono::milliseconds(50)); // 50ms polling delay
        }
    }
    
    void run() {
        // Initialize system
        program_init();
        
        // Start sensor loop in separate thread
        std::thread sensor_thread(&DirectionalENose::sensor_loop, this);
        
        // Start GUI (main thread)
        start_gui();
        
        // Wait for sensor thread to finish
        if (sensor_thread.joinable()) {
            sensor_thread.join();
        }
        
        // Handle shutdown
        if (shutdown.load()) {
            std::cout << "Shutdown flag is set. Closing app and shutting down..." << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(2));
            std::system("sudo shutdown now");
        } else {
            std::cout << "Shutdown not triggered. Closing app and staying powered on." << std::endl;
        }
    }

private:
    void init_bme680() {
        // Placeholder for BME680 initialization
        // Would need actual BME680 C++ library
        std::cout << "BME680 sensor initialized." << std::endl;
    }
    
    void init_sgp30_sensors() {
        // Placeholder for SGP30 initialization
        // Would need actual I2C communication setup
        std::cout << "SGP30 sensors initialized." << std::endl;
    }
    
    std::pair<int, int> read_sgp30_sensor(int sensor_index) {
        // Placeholder for actual sensor reading
        // Would need I2C communication with TCA9548A multiplexer
        // This is just dummy data for compilation
        return {400 + sensor_index * 100, sensor_index * 50};
    }
    
    void read_bme680_data() {
        // Placeholder for BME680 data reading
        std::cout << "Reading BME680 data..." << std::endl;
    }
    
    bool read_gpio(int pin) {
        // Try to read GPIO, return true if wiringPi not available
        try {
            return digitalRead(pin);
        } catch (...) {
            // If GPIO reading fails, return HIGH (button not pressed)
            return true;
        }
    }
    
    void clear_all_leds() {
        // Placeholder for LED control
        // Would use rpi_ws281x library
        std::cout << "Clearing all LEDs." << std::endl;
    }
    
    void set_led_color(int led_index, int color) {
        // Placeholder for LED control
        std::cout << "Setting LED " << led_index << " to color " << std::hex << color << std::endl;
    }
    
    void print_sensor_data() {
        std::cout << std::string(50, '-') << std::endl;
        for (size_t i = 0; i < co2_readings.size(); i++) {
            if (co2_readings[i] != -1 && tvoc_readings[i] != -1) {
                std::cout << "SGP30_" << (i+1) << ": CO2=" << co2_readings[i] 
                         << "ppm, TVOC=" << tvoc_readings[i] << "ppb" << std::endl;
            } else {
                std::cout << "SGP30_" << (i+1) << ": Error reading sensor" << std::endl;
            }
        }
        std::cout << std::string(50, '-') << std::endl;
    }
    
    void cleanup() {
        stop_event.store(true);
        // Additional cleanup if needed
    }
};

int main() {
    try {
        DirectionalENose enose;
        enose.run();
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
