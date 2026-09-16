#include <iostream>
#include <iomanip>
#include <vector>
#include <random>
#include <chrono>
#include <thread>
#include <cmath>
using namespace std;

struct Task {
    int id;
    double arrivalTime;
    double duration;
};

int main() {
    const int total = 1000;
    const int tickMs = 10;

    double lambda;
    double a;
    double b;

    cout << "Введите lambda: ";
    cin >> lambda;
    cout << "Введите a и b для времени обработки: ";
    cin >> a >> b;

    if (lambda <= 0 || a < 0 || b < a) {
        cout << "Ошибка: lambda > 0, a >= 0, b >= a" << endl;
        return 1;
    }

    mt19937 rng(random_device{}());
    exponential_distribution<double> arrivalGap(lambda);
    uniform_real_distribution<double> duration(a, b);

    vector<Task> lifoQueue;

    Task currentTask{0, 0.0, 0.0};
    bool serverBusy = false;

    auto start = chrono::steady_clock::now();

    double nextArrival = 0.0;
    double serverEndTime = 0.0;

    int created = 0;
    int finished = 0;

    double sumWaitingTime = 0.0;
    double sumSystemTime = 0.0;
    double sumSystemTimeSquare = 0.0;
    double queueLengthSum = 0.0;
    double lastTime = 0.0;

    while (finished < total) {
        double now = chrono::duration<double>(chrono::steady_clock::now() - start).count();
        queueLengthSum += lifoQueue.size() * (now - lastTime);
        lastTime = now;

        while (created < total && now >= nextArrival) {
            double taskDuration = duration(rng);

            lifoQueue.push_back(Task{created, nextArrival, taskDuration});
            created++;

            nextArrival += arrivalGap(rng);
        }

        if (serverBusy && serverEndTime <= now) {
            double systemTime = now - currentTask.arrivalTime;

            finished++;
            sumSystemTime += systemTime;
            sumSystemTimeSquare += systemTime * systemTime;
            serverBusy = false;
        }

        if (!serverBusy && !lifoQueue.empty()) {
            currentTask = lifoQueue.back();
            lifoQueue.pop_back();

            double waitingTime = now - currentTask.arrivalTime;
            sumWaitingTime += waitingTime;

            serverBusy = true;
            serverEndTime = now + currentTask.duration;
        }

        cout << "\rвремя: " << fixed << setprecision(1) << setw(5) << now
             << "с | сервер: ";
        if (serverBusy) {
            cout << "задача " << setw(4) << currentTask.id;
        } else {
            cout << "свободен   ";
        }
        cout << " | в очереди: " << setw(4) << lifoQueue.size()
             << " | создано: " << setw(4) << created
             << " | завершено: " << setw(4) << finished << "/" << total
             << "   " << flush;

        this_thread::sleep_for(chrono::milliseconds(tickMs));
    }

    double expectedSystemTime = sumSystemTime / total;
    double variance = sumSystemTimeSquare / total - expectedSystemTime * expectedSystemTime;
    if (variance < 0) {
        variance = 0;
    }
    double sigma = sqrt(variance);

    cout << fixed << setprecision(3);
    cout << "\n\nИтоги моделирования" << endl;
    cout << "Всего задач: " << total << endl;
    cout << "lambda: " << lambda << endl;
    cout << "Время обработки: от " << a << " до " << b << " сек" << endl;
    cout << "Дисциплина очереди: LIFO (последним пришел - первым обслужен)" << endl;
    cout << "Сервер: 1, одновременно выполняется только 1 задача" << endl;

    cout << "\nМатожидание - это среднее значение случайной величины." << endl;
    cout << "M(ожидание задачи в очереди): " << sumWaitingTime / total << " сек" << endl;
    cout << "M(время задачи в системе):    " << expectedSystemTime << " сек" << endl;
    cout << "СКО времени в системе:        " << sigma << " сек" << endl;
    cout << "M(длина очереди):             " << queueLengthSum / lastTime << endl;

    return 0;
}
