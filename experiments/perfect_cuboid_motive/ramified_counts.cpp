#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

using i64 = long long;

static int ipow_int(int a, int n) {
    int r = 1;
    while (n-- > 0) r *= a;
    return r;
}

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: ramified_counts OUTPUT.csv\n";
        return 2;
    }

    const std::vector<std::pair<int, int>> cases = {
        {3,1},{3,2},{3,3},{3,4},{3,5},{3,6},
        {5,1},{5,2},{5,3},{5,4},
        {7,1},{7,2},{7,3},{7,4},
        {11,1},{11,2},{11,3},
        {13,1},{13,2},{13,3},
        {17,1},{17,2},
        {19,1},{19,2},
        {23,1},{23,2},
        {29,1},{29,2},
        {31,1},{31,2},
        {37,1},{37,2}
    };

    std::ofstream out(argv[1]);
    if (!out) throw std::runtime_error("cannot open output");
    out << "p,m,modulus,euler,full,rejected,q3_zero,q3_nonzero_square,q3_nonsquare,"
           "redundant,survival_numerator,survival_denominator\n";

    for (const auto [p, m] : cases) {
        const int modulus = ipow_int(p, m);
        std::vector<char> square(modulus, 0);
        for (i64 x = 0; x < modulus; ++x) {
            square[static_cast<int>(x * x % modulus)] = 1;
        }

        i64 euler = 0;
        i64 full = 0;
        i64 q3_zero = 0;
        i64 q3_nonzero_square = 0;
        i64 q3_nonsquare = 0;

        for (int b = 0; b < modulus; ++b) {
            const int bb = static_cast<int>(1LL * b * b % modulus);
            const int q0 = (1 + bb) % modulus;
            if (!square[q0]) continue;

            for (int c = 0; c < modulus; ++c) {
                const int cc = static_cast<int>(1LL * c * c % modulus);
                const int q1 = (1 + cc) % modulus;
                const int q2 = (bb + cc) % modulus;
                if (!square[q1] || !square[q2]) continue;

                ++euler;
                const int q3 = (1 + bb + cc) % modulus;
                if (q3 == 0) {
                    ++q3_zero;
                }
                if (square[q3]) {
                    ++full;
                    if (q3 != 0) ++q3_nonzero_square;
                } else {
                    ++q3_nonsquare;
                }
            }
        }

        const i64 rejected = euler - full;
        if (q3_zero + q3_nonzero_square + q3_nonsquare != euler) {
            throw std::runtime_error("q3 partition failed");
        }

        out << p << ',' << m << ',' << modulus << ',' << euler << ',' << full << ','
            << rejected << ',' << q3_zero << ',' << q3_nonzero_square << ','
            << q3_nonsquare << ',' << (euler == full ? 1 : 0) << ','
            << full << ',' << euler << '\n';

        std::cerr << "RING p=" << p << " m=" << m << " q=" << modulus
                  << " E=" << euler << " F=" << full << " R=" << rejected << '\n';
    }

    return 0;
}
