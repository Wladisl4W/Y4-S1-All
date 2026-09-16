#include <iostream>
#include <utility>
#include <vector>
using namespace std;

int main() {
    int n;
    cout << "Введите количество событий: ";
    cin >> n;

    vector<pair<int, double>> events(n);

    for (int i = 0; i < n; i++) {
        cout << "Событие " << i + 1 << ": ";
        cin >> events[i].first >> events[i].second;
    }

    for (int i = 0; i < n - 1; i++) {
        for (int j = 0; j < n - i - 1; j++) {
            if (events[j].second > events[j + 1].second) {
                swap(events[j], events[j + 1]);
            }
        }
    }

    cout << "\nОтсортированные события:" << endl;
    for (int i = 0; i < n; i++) {
        cout << "ID: " << events[i].first << ", Время: " << events[i].second << " сек" << endl;
    }

    return 0;
}
