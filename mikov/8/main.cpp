#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <vector>
using namespace std;

struct Point {
    double x;
    double y;
};

const double circleRadius = 60.0;
const int experiments = 100000;
const double pi = acos(-1.0);

// Случайная точка равномерно по площади круга.
Point randomPoint(mt19937& generator) {
    uniform_real_distribution<double> uniform(0.0, 1.0);
    double distance = circleRadius * sqrt(uniform(generator));
    double angle = 2.0 * pi * uniform(generator);
    return {distance * cos(angle), distance * sin(angle)};
}

// Стенка лежит на оси X от (0, 0) до (60, 0).
bool crossesWall(const Point& a, const Point& b) {
    if (a.y == 0.0 && b.y == 0.0)
        return max(a.x, b.x) >= 0.0 && min(a.x, b.x) <= circleRadius;
    if ((a.y > 0 && b.y > 0) || (a.y < 0 && b.y < 0)) return false;
    double crossingX = (a.x * b.y - b.x * a.y) / (b.y - a.y);
    return crossingX >= 0.0 && crossingX <= circleRadius;
}

bool canConnect(const Point& a, const Point& b, double range) {
    double dx = a.x - b.x;
    double dy = a.y - b.y;
    return dx * dx + dy * dy <= range * range && !crossesWall(a, b);
}

bool networkIsConnected(int nodeCount, double range, mt19937& generator) {
    vector<Point> nodes;
    for (int i = 0; i < nodeCount; ++i) nodes.push_back(randomPoint(generator));

    vector<vector<int>> neighbors(nodeCount);
    for (int i = 0; i < nodeCount; ++i) {
        for (int j = 0; j < i; ++j) {
            if (canConnect(nodes[i], nodes[j], range)) {
                neighbors[i].push_back(j);
                neighbors[j].push_back(i);
            }
        }
    }

    vector<bool> visited(nodeCount, false);
    vector<int> stack = {0};
    visited[0] = true;
    int reached = 0;
    while (!stack.empty()) {
        int current = stack.back();
        stack.pop_back();
        ++reached;
        for (int next : neighbors[current]) {
            if (!visited[next]) {
                visited[next] = true;
                stack.push_back(next);
            }
        }
    }
    return reached == nodeCount;
}

int main() {
    mt19937 generator(20261111); // постоянное зерно для воспроизводимости
    ofstream file("connectivity.csv");
    if (!file) {
        cerr << "Не удалось создать connectivity.csv\n";
        return 1;
    }
    file << "n,r,connected,total,probability\n";
    file << fixed << setprecision(4);
    cout << fixed << setprecision(4);

    for (double range : {25.0, 35.0, 45.0, 55.0, 65.0}) {
        cout << "\nРадиус связи r = " << range << '\n';
        for (int nodeCount = 5; nodeCount <= 40; ++nodeCount) {
            int connected = 0;
            for (int trial = 0; trial < experiments; ++trial)
                if (networkIsConnected(nodeCount, range, generator)) ++connected;
            double probability = double(connected) / experiments;
            file << nodeCount << ',' << range << ',' << connected << ','
                 << experiments << ',' << probability << '\n';
            cout << "n=" << setw(2) << nodeCount << ": " << connected
                 << '/' << experiments << " = " << probability << '\n';
        }
    }
    cout << "\nРезультаты записаны в connectivity.csv\n";
    return 0;
}
