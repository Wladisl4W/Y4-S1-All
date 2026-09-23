#include <algorithm>
#include <cmath>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <random>
#include <string>
#include <vector>

using namespace std;

struct Event {
    int streamId;
    double time;
};

struct Statistics {
    size_t eventCount;
    double lambda;
    double sampleMean;
    double theoreticalMean;
    double coefficientOfVariation;
    double distributionError;
};

Statistics runExperiment(int streamCount, double a, double b,
                         int eventsPerStream, mt19937& rng) {
    const double sourceMean = (a + b) / 2.0;
    const double sourceLambda = 1.0 / sourceMean;
    const double totalLambda = streamCount * sourceLambda;
    const double observationTime = eventsPerStream * sourceMean;
    const double warmupTime = max(100.0 * sourceMean, observationTime * 0.1);

    uniform_real_distribution<double> intervalDistribution(a, b);
    uniform_real_distribution<double> initialPhase(0.0, sourceMean);
    vector<Event> events;
    events.reserve(static_cast<size_t>(streamCount) * eventsPerStream);

    for (int streamId = 1; streamId <= streamCount; ++streamId) {
        double eventTime = -warmupTime - initialPhase(rng);

        while (eventTime <= observationTime) {
            eventTime += intervalDistribution(rng);
            if (eventTime >= 0.0 && eventTime <= observationTime) {
                events.push_back({streamId, eventTime});
            }
        }
    }

    sort(events.begin(), events.end(), [](const Event& left, const Event& right) {
        return left.time < right.time;
    });

    vector<double> intervals;
    intervals.reserve(events.size() - 1);
    for (size_t i = 1; i < events.size(); ++i) {
        intervals.push_back(events[i].time - events[i - 1].time);
    }

    double sum = 0.0;
    double squareSum = 0.0;
    for (double interval : intervals) {
        sum += interval;
        squareSum += interval * interval;
    }

    const double sampleMean = sum / intervals.size();
    double variance = squareSum / intervals.size() - sampleMean * sampleMean;
    variance = max(0.0, variance);
    const double coefficientOfVariation = sqrt(variance) / sampleMean;

    vector<double> sortedIntervals = intervals;
    sort(sortedIntervals.begin(), sortedIntervals.end());

    double distributionError = 0.0;
    for (size_t i = 0; i < sortedIntervals.size(); ++i) {
        const double x = sortedIntervals[i];
        const double theoretical = 1.0 - exp(-totalLambda * x);
        const double empiricalBefore = static_cast<double>(i) / sortedIntervals.size();
        const double empiricalAfter = static_cast<double>(i + 1) / sortedIntervals.size();
        distributionError = max({
            distributionError,
            abs(empiricalBefore - theoretical),
            abs(empiricalAfter - theoretical)
        });
    }

    const int binCount = 60;
    const double maxX = 5.0 / totalLambda;
    const double binWidth = maxX / binCount;
    vector<int> bins(binCount, 0);

    for (double interval : intervals) {
        const int index = static_cast<int>(interval / binWidth);
        if (index >= 0 && index < binCount) {
            ++bins[index];
        }
    }

    const string fileName = "distribution_N" + to_string(streamCount) + ".csv";
    ofstream output(fileName);
    output << "density_x,empirical_density,theoretical_density,"
           << "cdf_x,empirical_cdf,theoretical_cdf\n";
    output << fixed << setprecision(8);

    for (int i = 0; i < binCount; ++i) {
        const double x = (i + 0.5) * binWidth;
        const double rightBoundary = (i + 1) * binWidth;
        const double empiricalDensity =
            static_cast<double>(bins[i]) / (intervals.size() * binWidth);
        const double theoreticalDensity = totalLambda * exp(-totalLambda * x);
        const double empiricalCdf = static_cast<double>(
            upper_bound(sortedIntervals.begin(), sortedIntervals.end(), rightBoundary)
            - sortedIntervals.begin()) / sortedIntervals.size();
        const double theoreticalCdf = 1.0 - exp(-totalLambda * rightBoundary);

        output << x << ',' << empiricalDensity << ',' << theoreticalDensity << ','
               << rightBoundary << ',' << empiricalCdf << ',' << theoreticalCdf << '\n';
    }

    return {
        events.size(),
        totalLambda,
        sampleMean,
        1.0 / totalLambda,
        coefficientOfVariation,
        distributionError
    };
}

int main() {
    double a;
    double b;
    int eventsPerStream;
    int experimentCount;

    cout << "Введите границы равномерного распределения a и b: ";
    cin >> a >> b;
    cout << "Введите примерное число событий в одном потоке: ";
    cin >> eventsPerStream;
    cout << "Введите количество экспериментов: ";
    cin >> experimentCount;

    if (!cin || a < 0.0 || b < a || b == 0.0 || eventsPerStream < 100
        || experimentCount <= 0) {
        cout << "Ошибка: требуется 0 <= a <= b, b > 0, не менее 100 событий "
             << "и положительное число экспериментов." << endl;
        return 1;
    }

    vector<int> streamCounts(experimentCount);
    cout << "Введите значения N для каждого эксперимента: ";
    for (int& streamCount : streamCounts) {
        cin >> streamCount;
        if (!cin || streamCount <= 0) {
            cout << "Ошибка: N должно быть положительным." << endl;
            return 1;
        }
    }

    mt19937 rng(random_device{}());

    cout << fixed << setprecision(6);
    cout << "\nСравнение интервалов суперпозиции с экспоненциальным распределением\n";
    cout << "N; событий; lambda; M выборочное; M теоретическое; "
         << "коэффициент вариации; ошибка F\n";

    for (int streamCount : streamCounts) {
        const Statistics statistics = runExperiment(
            streamCount, a, b, eventsPerStream, rng);

        cout << streamCount << "; "
             << statistics.eventCount << "; "
             << statistics.lambda << "; "
             << statistics.sampleMean << "; "
             << statistics.theoreticalMean << "; "
             << statistics.coefficientOfVariation << "; "
             << statistics.distributionError << '\n';
    }

    cout << "\nДля экспоненциального распределения коэффициент вариации равен 1." << endl;
    cout << "Ошибка F — максимальное расхождение эмпирической и теоретической "
         << "функций распределения." << endl;
    cout << "Данные плотности и функции распределения записаны в файлы "
         << "distribution_N*.csv." << endl;

    return 0;
}
