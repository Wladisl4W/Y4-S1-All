#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <random>
using namespace std;

const int repetitions = 10000;
struct Case { double lambdaRate; double muRate; };

// Один независимый запуск модели от пустой системы до момента stopTime.
bool serverIsFree(double stopTime, const Case& parameters, mt19937& generator) {
    exponential_distribution<double> arrivalGap(parameters.lambdaRate);
    exponential_distribution<double> serviceTime(parameters.muRate);
    const double infinity = numeric_limits<double>::infinity();

    int customers = 0; // число заявок в системе: на обслуживании и в очереди
    double nextArrival = arrivalGap(generator);
    double nextFinish = infinity;

    while (nextArrival <= stopTime || nextFinish <= stopTime) {
        if (nextArrival < nextFinish) {
            // Пришла заявка. Если сервер пуст, сразу начинаем обслуживание.
            if (customers == 0)
                nextFinish = nextArrival + serviceTime(generator);
            ++customers;
            nextArrival += arrivalGap(generator);
        } else {
            // Завершилось обслуживание. Берём следующую заявку из очереди.
            --customers;
            if (customers > 0)
                nextFinish += serviceTime(generator);
            else
                nextFinish = infinity;
        }
    }
    return customers == 0;
}

int countFree(int stopTime, const Case& parameters, mt19937& generator) {
    int freeCount = 0;
    for (int run = 0; run < repetitions; ++run)
        if (serverIsFree(stopTime, parameters, generator)) ++freeCount;
    return freeCount;
}

int main() {
    mt19937 generator(20261028); // постоянное зерно для повторяемых результатов
    ofstream file("free_probability.csv");
    if (!file) {
        cerr << "Не удалось создать free_probability.csv\n";
        return 1;
    }
    file << "case,lambda,mu,time,free_count,busy_count,free_probability\n";
    const Case cases[] = {{0.4, 1.0}, {0.6, 1.0}, {0.8, 1.0},
                          {0.6, 1.2}, {0.8, 1.2}};
    cout << "M/M/1: 5 наборов коэффициентов, " << repetitions
         << " повторений для каждого t\n";
    cout << fixed << setprecision(4);
    for (int caseNumber = 0; caseNumber < 5; ++caseNumber) {
        const Case& parameters = cases[caseNumber];
        cout << "\nСлучай " << caseNumber + 1 << ": lambda=" << parameters.lambdaRate
             << ", mu=" << parameters.muRate << '\n';
        for (int t = 0; t <= 30; ++t) {
            int freeCount = countFree(t, parameters, generator);
            int busyCount = repetitions - freeCount;
            double probability = double(freeCount) / repetitions;
            file << caseNumber + 1 << ',' << parameters.lambdaRate << ','
                 << parameters.muRate << ',' << t << ',' << freeCount << ','
                 << busyCount << ',' << probability << '\n';
            cout << "t=" << setw(2) << t << ": свободен " << setw(5) << freeCount
                 << ", занят " << setw(5) << busyCount
                 << ", доля свободных " << probability << '\n';
        }
        cout << "Теоретический предел: "
             << 1 - parameters.lambdaRate / parameters.muRate << '\n';
    }
}
