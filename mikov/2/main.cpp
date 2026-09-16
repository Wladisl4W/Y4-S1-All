#include <iostream>
#include <iomanip>
#include <vector>
#include <random>
#include <chrono>
#include <thread>
using namespace std;

struct Task {
    int id;
    double endTime;
};

int main() {
    const int total = 1000;
    const int tickMs = 10;

    mt19937 rng(random_device{}());
    uniform_real_distribution<double> duration(0.6, 1.8);
    uniform_real_distribution<double> arrivalGap(0.2, 0.6);

    vector<Task> running;
    auto start = chrono::steady_clock::now();

    double nextArrival = 0;
    int created = 0;
    int finished = 0;

    while (finished < total) {
        double now = chrono::duration<double>(chrono::steady_clock::now() - start).count();

        if (created < total && now >= nextArrival) {
            running.push_back(Task{created, now + duration(rng)});
            created++;
            nextArrival = now + arrivalGap(rng);
        }

        for (size_t i = 0; i < running.size(); ) {
            if (running[i].endTime <= now) {
                running.erase(running.begin() + i);
                finished++;
            } else {
                i++;
            }
        }

        cout << "\rвремя: " << fixed << setprecision(1) << setw(5) << now
             << "с | выполняется: " << setw(4) << running.size() << " | ID:";
        if (running.empty()) {
            cout << " нет";
        } else {
            for (size_t i = 0; i < running.size(); i++) {
                cout << " " << running[i].id;
            }
        }
        cout << " | завершено: " << setw(4) << finished << "/" << total
             << "   " << flush;

        this_thread::sleep_for(chrono::milliseconds(tickMs));
    }

    return 0;
}
