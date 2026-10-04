#include <algorithm>
#include <cmath>
#include <iomanip>
#include <iostream>
#include <queue>
#include <random>
#include <vector>
using namespace std;

struct Task {
    int id;
    double arrivalTime;
    double duration;
};

struct Result {
    double meanWaiting;
    double sigmaWaiting;
    vector<int> firstServers;
    vector<double> firstStarts;
};

Result simulate(const vector<Task>& tasks, bool randomRouting, mt19937& rng) {
    queue<Task> queues[3];
    uniform_int_distribution<int> serverChoice(0, 2);
    Result result{};

    for (const Task& task : tasks) {
        int server = randomRouting ? serverChoice(rng) : task.id % 3;
        queues[server].push(task);
        if (task.id < 6) {
            result.firstServers.push_back(server + 1);
        }
    }

    double freeTime[3] = {0.0, 0.0, 0.0};
    double waitingSum = 0.0;
    double waitingSquareSum = 0.0;
    result.firstStarts.resize(6);

    // У каждого сервера свое время освобождения, поэтому они работают параллельно.
    for (int server = 0; server < 3; ++server) {
        while (!queues[server].empty()) {
            Task task = queues[server].front();
            queues[server].pop();

            double startTime = max(task.arrivalTime, freeTime[server]);
            double waiting = startTime - task.arrivalTime;
            freeTime[server] = startTime + task.duration;

            waitingSum += waiting;
            waitingSquareSum += waiting * waiting;
            if (task.id < 6) {
                result.firstStarts[task.id] = startTime;
            }
        }
    }

    result.meanWaiting = waitingSum / tasks.size();
    double variance = waitingSquareSum / tasks.size()
        - result.meanWaiting * result.meanWaiting;
    result.sigmaWaiting = sqrt(max(0.0, variance));
    return result;
}

void printResult(const char* name, const Result& result,
                 const vector<Task>& tasks) {
    cout << "\n" << name << endl;
    cout << "Среднее ожидание в очереди: " << result.meanWaiting << " сек" << endl;
    cout << "СКО ожидания в очереди:    " << result.sigmaWaiting << " сек" << endl;
    cout << "Первые задачи (ID, сервер, приход, начало):" << endl;
    for (int i = 0; i < 6; ++i) {
        cout << i << ", " << result.firstServers[i] << ", "
             << tasks[i].arrivalTime << ", " << result.firstStarts[i] << endl;
    }
}

int main() {
    const int total = 100000;
    double lambda;
    double mu;

    cout << "Введите lambda (интенсивность входного потока): ";
    cin >> lambda;
    cout << "Введите mu (интенсивность обработки одного сервера): ";
    cin >> mu;

    if (!cin || !isfinite(lambda) || !isfinite(mu)
        || lambda <= 0.0 || mu <= 0.0 || lambda / 3.0 >= mu) {
        cout << "Ошибка: нужны конечные lambda > 0, mu > 0 и lambda < 3 * mu" << endl;
        return 1;
    }

    mt19937 rng(random_device{}());
    exponential_distribution<double> arrivalGap(lambda);
    exponential_distribution<double> duration(mu);
    vector<Task> tasks;
    tasks.reserve(total);

    double arrivalTime = 0.0;
    for (int i = 0; i < total; ++i) {
        arrivalTime += arrivalGap(rng);
        tasks.push_back({i, arrivalTime, duration(rng)});
    }

    Result cyclic = simulate(tasks, false, rng);
    Result random = simulate(tasks, true, rng);

    cout << fixed << setprecision(4);
    cout << "\nЗадач: " << total << ", серверов: 3, отдельные очереди FIFO" << endl;
    cout << "lambda = " << lambda << ", mu = " << mu << endl;
    cout << "Время обработки в обоих вариантах одинаково для каждой задачи." << endl;
    printResult("Циклическое распределение", cyclic, tasks);
    printResult("Случайное распределение (вероятность 1/3)", random, tasks);

    cout << "\nВывод: ";
    if (cyclic.meanWaiting == random.meanWaiting
        && cyclic.sigmaWaiting == random.sigmaWaiting) {
        cout << "по обоим показателям результаты равны." << endl;
    } else if (cyclic.meanWaiting <= random.meanWaiting
               && cyclic.sigmaWaiting <= random.sigmaWaiting) {
        cout << "циклическое распределение лучше по обоим показателям." << endl;
    } else if (random.meanWaiting <= cyclic.meanWaiting
               && random.sigmaWaiting <= cyclic.sigmaWaiting) {
        cout << "случайное распределение лучше по обоим показателям." << endl;
    } else {
        cout << "один вариант лучше по среднему, другой по СКО." << endl;
    }

    return 0;
}
