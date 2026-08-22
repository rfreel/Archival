#include <algorithm>
#include <array>
#include <cstdint>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

using i64 = long long;

static int imod(i64 x, int m) {
    x %= m;
    if (x < 0) x += m;
    return static_cast<int>(x);
}

static int ipow_int(int a, int n) {
    int r = 1;
    while (n-- > 0) r *= a;
    return r;
}

static bool polynomial_divides(
    const std::vector<int>& f,
    const std::vector<int>& g,
    int p
) {
    std::vector<int> rem = f;
    const int nf = static_cast<int>(f.size()) - 1;
    const int ng = static_cast<int>(g.size()) - 1;
    for (int k = nf; k >= ng; --k) {
        const int c = rem[k];
        if (c == 0) continue;
        for (int j = 0; j <= ng; ++j) {
            rem[k - ng + j] = imod(rem[k - ng + j] - 1LL * c * g[j], p);
        }
    }
    for (int i = 0; i < ng; ++i) if (rem[i] != 0) return false;
    return true;
}

static std::vector<int> find_irducible(int p, int n) {
    if (n == 1) return {0, 1};
    const int count = ipow_int(p, n);
    for (int code = 0; code < count; ++code) {
        std::vector<int> f(n + 1, 0);
        int x = code;
        for (int i = 0; i < n; ++i) {
            f[i] = x % p;
            x /= p;
        }
        f[n] = 1;
        if (f[0] == 0) continue;

        bool reducible = false;
        for (int d = 1; d <= n / 2 && !reducible; ++d) {
            const int divisors = ipow_int(p, d);
            for (int gc = 0; gc < divisors; ++gc) {
                std::vector<int> g(d + 1, 0);
                int y = gc;
                for (int i = 0; i < d; ++i) {
                    g[i] = y % p;
                    y /= p;
                }
                g[d] = 1;
                if (g[0] == 0) continue;
                if (polynomial_divides(f, g, p)) {
                    reducible = true;
                    break;
                }
            }
        }
        if (!reducible) return f;
    }
    throw std::runtime_error("no irreducible polynomial");
}

class UnramifiedQuotient {
public:
    int p;
    int n;
    int m;
    int coefficient_modulus;
    int size;
    std::vector<int> polynomial;
    std::vector<int> square;
    std::vector<char> is_square;
    std::vector<int> add_table;
    std::vector<int> add_one;

    UnramifiedQuotient(int prime, int residue_degree, int depth)
        : p(prime), n(residue_degree), m(depth),
          coefficient_modulus(ipow_int(prime, depth)),
          size(ipow_int(coefficient_modulus, residue_degree)),
          polynomial(find_irducible(prime, residue_degree)) {
        square.resize(size);
        is_square.assign(size, 0);
        add_one.resize(size);

        for (int x = 0; x < size; ++x) {
            square[x] = mul(x, x);
            is_square[square[x]] = 1;
        }

        add_table.resize(static_cast<size_t>(size) * static_cast<size_t>(size));
        for (int a = 0; a < size; ++a) {
            for (int b = 0; b < size; ++b) {
                add_table[static_cast<size_t>(a) * size + b] = add_slow(a, b);
            }
        }
        for (int a = 0; a < size; ++a) add_one[a] = add(a, 1);
    }

    int add(int a, int b) const {
        return add_table[static_cast<size_t>(a) * size + b];
    }

    int mul(int a, int b) const {
        if (n == 1) return static_cast<int>(1LL * a * b % coefficient_modulus);

        std::vector<int> av(n), bv(n);
        int aa = a, bb = b;
        for (int i = 0; i < n; ++i) {
            av[i] = aa % coefficient_modulus;
            bv[i] = bb % coefficient_modulus;
            aa /= coefficient_modulus;
            bb /= coefficient_modulus;
        }

        std::vector<int> tmp(2 * n - 1, 0);
        for (int i = 0; i < n; ++i) {
            for (int j = 0; j < n; ++j) {
                tmp[i + j] = imod(
                    tmp[i + j] + 1LL * av[i] * bv[j],
                    coefficient_modulus
                );
            }
        }

        for (int k = 2 * n - 2; k >= n; --k) {
            const int c = tmp[k];
            if (c == 0) continue;
            for (int i = 0; i < n; ++i) {
                tmp[k - n + i] = imod(
                    tmp[k - n + i] - 1LL * c * polynomial[i],
                    coefficient_modulus
                );
            }
        }

        int out = 0;
        int place = 1;
        for (int i = 0; i < n; ++i) {
            out += tmp[i] * place;
            place *= coefficient_modulus;
        }
        return out;
    }

    std::string polynomial_string() const {
        if (n == 1) return "x";
        std::ostringstream out;
        out << "x^" << n;
        for (int i = n - 1; i >= 0; --i) {
            if (polynomial[i] == 0) continue;
            out << "+" << polynomial[i];
            if (i >= 1) out << "*x";
            if (i >= 2) out << "^" << i;
        }
        return out.str();
    }

private:
    int add_slow(int a, int b) const {
        if (n == 1) return (a + b) % coefficient_modulus;
        int out = 0;
        int place = 1;
        for (int i = 0; i < n; ++i) {
            const int digit = (a % coefficient_modulus + b % coefficient_modulus) % coefficient_modulus;
            a /= coefficient_modulus;
            b /= coefficient_modulus;
            out += digit * place;
            place *= coefficient_modulus;
        }
        return out;
    }
};

int main(int argc, char** argv) {
    if (argc != 2) {
        std::cerr << "usage: unramified_ring_grid OUTPUT.csv\n";
        return 2;
    }

    const std::vector<std::tuple<int, int, int>> cases = {
        {3,1,1},{3,1,2},{3,1,3},{3,1,4},
        {3,2,1},{3,2,2},{3,2,3},
        {3,3,1},{3,3,2},
        {5,1,1},{5,1,2},{5,1,3},
        {5,2,1},{5,2,2},
        {7,1,1},{7,1,2},{7,1,3},
        {7,2,1},{7,2,2},
        {11,1,1},{11,1,2},{11,1,3},
        {13,1,1},{13,1,2}
    };

    std::ofstream out(argv[1]);
    if (!out) throw std::runtime_error("cannot open output");
    out << "p,n,m,size,coefficient_modulus,polynomial,euler,full,rejected,"
           "q3_zero,q3_nonzero_square,q3_nonsquare,redundant\n";

    for (const auto [p, n, m] : cases) {
        UnramifiedQuotient R(p, n, m);
        i64 euler = 0;
        i64 full = 0;
        i64 q3_zero = 0;
        i64 q3_nonzero_square = 0;
        i64 q3_nonsquare = 0;

        for (int b = 0; b < R.size; ++b) {
            const int bb = R.square[b];
            const int q0 = R.add_one[bb];
            if (!R.is_square[q0]) continue;

            for (int c = 0; c < R.size; ++c) {
                const int cc = R.square[c];
                const int q1 = R.add_one[cc];
                const int q2 = R.add(bb, cc);
                if (!R.is_square[q1] || !R.is_square[q2]) continue;

                ++euler;
                const int q3 = R.add_one[q2];
                if (q3 == 0) ++q3_zero;
                if (R.is_square[q3]) {
                    ++full;
                    if (q3 != 0) ++q3_nonzero_square;
                } else {
                    ++q3_nonsquare;
                }
            }
        }

        if (q3_zero + q3_nonzero_square + q3_nonsquare != euler) {
            throw std::runtime_error("stratum partition failed");
        }

        out << p << ',' << n << ',' << m << ',' << R.size << ','
            << R.coefficient_modulus << ",\"" << R.polynomial_string() << "\"," 
            << euler << ',' << full << ',' << (euler - full) << ','
            << q3_zero << ',' << q3_nonzero_square << ',' << q3_nonsquare << ','
            << (euler == full ? 1 : 0) << '\n';

        std::cerr << "GRID p=" << p << " n=" << n << " m=" << m
                  << " size=" << R.size << " E=" << euler << " F=" << full
                  << " R=" << (euler - full) << '\n';
    }

    return 0;
}
