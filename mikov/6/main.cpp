#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <vector>
using namespace std;

// a2*x'' + a1*x' + a0*x = k*(1 - x(t-tau))
struct Parameters { double a2 = 1, a1 = 1, a0 = 1, k = 2, tau = 0; };
const double dt = 0.01;
const double totalTime = 300.0;

double simulate(const Parameters& p, const char* fileName = nullptr) {
    const int steps = int(totalTime / dt);
    const int delaySteps = int(round(p.tau / dt));
    vector<double> history(steps + 1, 0.0);
    ofstream output;
    if (fileName) { output.open(fileName); output << "time,x,goal\n"; }
    double x = 0, speed = 0, equilibrium = p.k / (p.a0 + p.k);
    double early = 0, late = 0;
    int earlyCount = 0, lateCount = 0;
    for (int i = 0; i <= steps; ++i) {
        double time = i * dt;
        if (fileName && i % 10 == 0) output << fixed << setprecision(4) << time << ',' << x << ",1\n";
        double error = x - equilibrium;
        if (time >= 180 && time < 230) { early += error * error; ++earlyCount; }
        if (time >= 250 && time < 300) { late += error * error; ++lateCount; }
        if (i == steps) break;
        int oldIndex = i - delaySteps;
        double oldX = oldIndex >= 0 ? history[oldIndex] : 0;
        double acceleration = (p.k * (1 - oldX) - p.a1 * speed - p.a0 * x) / p.a2;
        speed += dt * acceleration;
        x += dt * speed;
        history[i + 1] = x;
        if (!isfinite(x) || fabs(x) > 1e100) return 1e100;
    }
    double first = sqrt(early / earlyCount), second = sqrt(late / lateCount);
    if (first < 1e-12 && second < 1e-12) return 0;
    return second / (first + 1e-30);
}

double criticalDelay(Parameters p) {
    double left = 0, right = 0.5;
    p.tau = right;
    while (simulate(p) <= 1 && right < 8) { right *= 2; p.tau = right; }
    if (right >= 8 && simulate(p) <= 1) return -1;
    while (right - left > dt) {
        double middle = round((left + right) / (2 * dt)) * dt;
        if (middle <= left || middle >= right) break;
        p.tau = middle;
        if (simulate(p) > 1) right = middle; else left = middle;
    }
    return (left + right) / 2;
}

int main() {
    ofstream table("critical_delay.csv");
    table << "a1,k,critical_tau\n";
    cout << fixed << setprecision(3);
    for (double a1 : {0.5, 1.0, 1.5})
        for (double k : {1.5, 2.0, 2.5, 3.0, 3.5, 4.0}) {
            Parameters p; p.a1 = a1; p.k = k;
            double boundary = criticalDelay(p);
            table << a1 << ',' << k << ',' << boundary << '\n';
            cout << "a1=" << a1 << " k=" << k << " critical tau=" << boundary << '\n';
        }
    Parameters p;
    double boundary = criticalDelay(p);
    p.tau = 0; simulate(p, "response_no_delay.csv");
    p.tau = boundary - 0.15; simulate(p, "response_stable.csv");
    p.tau = boundary + 0.15; simulate(p, "response_unstable.csv");
    cout << "Example: stable tau=" << boundary - 0.15
         << ", unstable tau=" << boundary + 0.15 << '\n';
}
